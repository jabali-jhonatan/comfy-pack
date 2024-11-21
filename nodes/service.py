from __future__ import annotations

import json
import logging
import os
import shutil
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

with open(WORKFLOW_FILE, "r") as f:
    workflow = json.load(f)

InputModel = comfy_pack.generate_input_model(workflow)
app = fastapi.FastAPI()


@lru_cache
def _get_workspace() -> Path:  # TODO: standardize bento run path in bentoml
    from bentoml._internal.configuration.containers import BentoMLContainer

    if bento := ComfyService.bento:
        wp = (
            Path(BentoMLContainer.bentoml_home.get())
            / "run"
            / str(bento.tag).replace(":", "-")
            / "comfy_workspace"
        )
        wp.parent.mkdir(parents=True, exist_ok=True)
    else:
        wp = Path.cwd() / "comfy_workspace"
    return wp


@app.get("/workflow.json")
def workflow_json():
    return workflow


@bentoml.mount_asgi_app(app, path="/comfy")
@bentoml.service(traffic={"timeout": REQUEST_TIMEOUT * 2})
class ComfyService:
    def __init__(self):
        self.comfy_proc = comfy_pack.run.WorkflowRunner(
            str(_get_workspace()), str(INPUT_DIR)
        )
        self.comfy_proc.start(verbose=int("BENTOML_DEBUG" in os.environ))

    @bentoml.api(input_spec=InputModel)
    def generate(
        self,
        *,
        ctx: bentoml.Context,
        **kwargs: Any,
    ) -> Path:
        verbose = int("BENTOML_DEBUG" in os.environ)
        ret = self.comfy_proc.run_workflow(
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
        self.comfy_proc.stop()

    @bentoml.on_deployment
    @staticmethod
    def prepare_comfy_workspace():
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
            install_custom_modules(snapshot, comfy_workspace, verbose=verbose)
            comfy_workspace.joinpath(".DONE").touch()
