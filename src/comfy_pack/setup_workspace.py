#!/usr/bin/env python3
# ruff: noqa: E402
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

virtualenv = os.environ.get("VIRTUAL_ENV")
if virtualenv and "--reload" not in sys.argv:
    print("Re-executing in virtualenv:", virtualenv)
    venv_python = os.path.join(virtualenv, "bin/python3")
    os.execl(venv_python, venv_python, *sys.argv, "--reload")

# The script path is ./env/docker/setup_script
SRC_DIR = Path(__file__).parent.parent.parent / "src"
INPUT_DIR = SRC_DIR / "input"
sys.path.append(str(SRC_DIR))


def _get_workspace() -> tuple[Path, dict]:
    import hashlib
    import json

    from bentoml._internal.configuration.containers import BentoMLContainer

    snapshot = SRC_DIR / "snapshot.json"
    checksum = hashlib.md5(snapshot.read_bytes()).hexdigest()
    wp = (
        Path(BentoMLContainer.bentoml_home.get()) / "run" / "comfy_workspace" / checksum
    )
    wp.parent.mkdir(parents=True, exist_ok=True)
    return wp, json.loads(snapshot.read_text())


def prepare_comfy_workspace():
    import shutil

    from comfy_pack.package import install_comfyui, install_custom_modules

    verbose = int("BENTOML_DEBUG" in os.environ)
    comfy_workspace, snapshot = _get_workspace()

    if not comfy_workspace.joinpath(".DONE").exists():
        if comfy_workspace.exists():
            print("Removing existing workspace")
            shutil.rmtree(comfy_workspace, ignore_errors=True)
        install_comfyui(snapshot, comfy_workspace, verbose=verbose)

        for f in INPUT_DIR.glob("*"):
            if f.is_file():
                shutil.copy(f, comfy_workspace / "input" / f.name)
            elif f.is_dir():
                shutil.copytree(f, comfy_workspace / "input" / f.name)

        install_custom_modules(snapshot, comfy_workspace, verbose=verbose)
        comfy_workspace.joinpath(".DONE").touch()
        subprocess.run(
            ["chown", "-R", "bentoml:bentoml", str(comfy_workspace)], check=True
        )


if __name__ == "__main__":
    prepare_comfy_workspace()
