from __future__ import annotations

import contextlib
import json
import logging
import os
import shutil
import signal
import threading
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

import bentoml
import fastapi

import comfy_pack
import comfy_pack.run

REQUEST_TIMEOUT = 360
BASE_DIR = Path(__file__).parent
WORKFLOW_FILE = BASE_DIR / "workflow_api.json"
COPY_THRESHOLD = 10 * 1024 * 1024
INPUT_DIR = BASE_DIR / "input"
logger = logging.getLogger("bentoml.service")


EXISTING_COMFYUI_SERVER = os.environ.get("COMFYUI_SERVER")


with open(WORKFLOW_FILE, "r") as f:
    workflow = json.load(f)

InputModel = comfy_pack.generate_input_model(workflow)
app = fastapi.FastAPI()


@lru_cache
def _get_workspace() -> Path:
    import hashlib

    from bentoml._internal.configuration.containers import BentoMLContainer

    snapshot = BASE_DIR / "snapshot.json"
    checksum = hashlib.md5(snapshot.read_bytes()).hexdigest()
    wp = (
        Path(BentoMLContainer.bentoml_home.get()) / "run" / "comfy_workspace" / checksum
    )
    wp.parent.mkdir(parents=True, exist_ok=True)
    return wp


@app.get("/workflow.json")
def workflow_json():
    return workflow


def _watch_server(server: comfy_pack.run.ComfyUIServer):
    while True:
        time.sleep(1)
        if not server.is_running():
            os.kill(os.getpid(), signal.SIGTERM)


@bentoml.mount_asgi_app(app, path="/comfy")
@bentoml.service(traffic={"timeout": REQUEST_TIMEOUT * 2}, resources={"gpu": 1})
class ComfyService:
    def __init__(self):
        print("EXISTING_COMFYUI_SERVER", EXISTING_COMFYUI_SERVER)
        if not EXISTING_COMFYUI_SERVER:
            self.server_stack = contextlib.ExitStack()
            self.server = self.server_stack.enter_context(
                comfy_pack.run.ComfyUIServer(
                    str(_get_workspace()),
                    str(INPUT_DIR),
                    verbose=int("BENTOML_DEBUG" in os.environ),
                )
            )
            print("ComfyUI Server started at", self.server.host, self.server.port)
            self.host = self.server.host
            self.port = self.server.port
            self.watch_thread = threading.Thread(
                target=_watch_server,
                args=(self.server,),
                daemon=True,
            )
            self.watch_thread.start()
            print("Watch thread started")
        else:
            if ":" in EXISTING_COMFYUI_SERVER:
                self.host, port = EXISTING_COMFYUI_SERVER.split(":")
                self.port = int(port)
            else:
                self.host = EXISTING_COMFYUI_SERVER
                self.port = 80

    @bentoml.api(input_spec=InputModel)
    def generate(
        self,
        *,
        ctx: bentoml.Context,
        **kwargs: Any,
    ) -> Path:
        verbose = int("BENTOML_DEBUG" in os.environ)
        ret = comfy_pack.run_workflow(
            self.host,
            self.port,
            workflow,
            output_dir=ctx.temp_dir,
            timeout=REQUEST_TIMEOUT,
            verbose=verbose,
            **kwargs,
        )
        if isinstance(ret, list):
            ret = ret[-1]
        return ret

    @bentoml.on_shutdown
    def on_shutdown(self):
        if not EXISTING_COMFYUI_SERVER:
            self.server_stack.close()

    @bentoml.on_deployment
    @staticmethod
    def prepare_comfy_workspace():
        if EXISTING_COMFYUI_SERVER:
            return

        from comfy_pack.package import install_comfyui, install_custom_modules

        verbose = int("BENTOML_DEBUG" in os.environ)
        comfy_workspace = _get_workspace()

        with BASE_DIR.joinpath("snapshot.json").open("rb") as f:
            snapshot = json.load(f)

        if not comfy_workspace.joinpath(".DONE").exists():
            if comfy_workspace.exists():
                logger.info("Removing existing workspace")
                shutil.rmtree(comfy_workspace, ignore_errors=True)
            install_comfyui(snapshot, comfy_workspace, verbose=verbose)

            for model in snapshot["models"]:
                if model.get("disabled", False):
                    continue
                model_tag = model.get("model_tag")
                if not model_tag:
                    logger.warning(
                        "Model %s is not in model store, the workflow may not work",
                        model["filename"],
                    )
                    continue
                model_path = comfy_workspace / cast(str, model["filename"])
                model_path.parent.mkdir(parents=True, exist_ok=True)
                bento_model = bentoml.models.get(model_tag)
                model_file = bento_model.path_of("model.bin")
                logger.info("Copying %s to %s", model_file, model_path)
                model_path.symlink_to(model_file)

            for f in INPUT_DIR.glob("*"):
                if f.is_file():
                    shutil.copy(f, comfy_workspace / "input" / f.name)
                elif f.is_dir():
                    shutil.copytree(f, comfy_workspace / "input" / f.name)

            install_custom_modules(snapshot, comfy_workspace, verbose=verbose)
            comfy_workspace.joinpath(".DONE").touch()
