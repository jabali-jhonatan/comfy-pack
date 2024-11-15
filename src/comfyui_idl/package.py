from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

COMFYUI_REPO = "https://github.com/comfyanonymous/ComfyUI.git"


def _clone_commit(url: str, commit: str, dir: Path):
    subprocess.check_call(["git", "clone", "--filter=blob:none", url, dir])
    subprocess.check_call(["git", "fetch", "-q", url, commit], cwd=dir)
    subprocess.check_call(["git", "checkout", "FETCH_HEAD"], cwd=dir)


def install_comfyui(snapshot, workspace: Path):
    print("Installing ComfyUI")
    comfyui_commit = snapshot["comfyui"]

    _clone_commit(COMFYUI_REPO, comfyui_commit, workspace)


def install_custom_modules(snapshot, workspace: Path):
    print("Installing custom nodes")
    for module in snapshot["custom_nodes"]:
        url = module["url"]
        directory = url.split("/")[-1].split(".")[0]
        module_dir = workspace / "custom_nodes" / directory

        commit_hash = module["commit_hash"]
        _clone_commit(url, commit_hash, module_dir)


def install_dependencies(snapshot: dict, req_file: str, workspace: Path):
    print("Installing Python dependencies")
    python_version = snapshot["python"]
    subprocess.check_call(
        ["uv", "python", "install", python_version],
        cwd=workspace,
    )
    venv = workspace / ".venv"
    if (venv / "DONE").exists():
        return
    venv_py = (
        venv / "Scripts" / "python.exe" if os.name == "nt" else venv / "bin" / "python"
    )
    subprocess.check_call(
        [
            "uv",
            "venv",
            "--python",
            python_version,
            venv,
        ],
    )
    subprocess.check_call(
        [
            "uv",
            "pip",
            "install",
            "-p",
            str(venv_py),
            "pip",
        ],
    )
    subprocess.check_call(
        [
            "uv",
            "pip",
            "install",
            "-p",
            str(venv_py),
            "-r",
            req_file,
            "--no-deps",
        ],
    )
    with open(venv / "DONE", "w") as f:
        f.write("DONE")


def install(cpack: str | Path, workspace: str | Path = "workspace") -> None:
    workspace = Path(workspace)
    with tempfile.TemporaryDirectory() as temp_dir:
        pack_dir = Path(temp_dir) / ".cpack"
        shutil.unpack_archive(cpack, pack_dir)
        snapshot = json.loads((pack_dir / "snapshot.json").read_text())
        req_txt_file = pack_dir / "requirements.txt"

        install_comfyui(snapshot, workspace)
        install_custom_modules(snapshot, workspace)
        install_dependencies(snapshot, str(req_txt_file), workspace)
        for f in (pack_dir / "inputs").glob("*"):
            shutil.copy(f, workspace / "input" / f.name)


if __name__ == "__main__":
    import sys

    install(sys.argv[1])
