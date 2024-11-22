from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

COMFYUI_REPO = "https://github.com/comfyanonymous/ComfyUI.git"


def _clone_commit(url: str, commit: str, dir: Path, verbose: int = 0):
    stdout = None if verbose > 0 else subprocess.DEVNULL
    stderr = None if verbose > 1 else subprocess.DEVNULL
    subprocess.check_call(
        ["git", "clone", "--recurse-submodules", "--filter=blob:none", url, dir],
        stdout=stdout,
        stderr=stderr,
    )
    subprocess.check_call(
        ["git", "fetch", "-q", url, commit],
        cwd=dir,
        stdout=stdout,
        stderr=stderr,
    )
    subprocess.check_call(
        ["git", "checkout", "FETCH_HEAD"],
        cwd=dir,
        stdout=stdout,
        stderr=stderr,
    )
    subprocess.check_call(
        ["git", "submodule", "update", "--init", "--recursive"],
        cwd=dir,
        stdout=stdout,
        stderr=stderr,
    )


def install_comfyui(snapshot, workspace: Path, verbose: int = 0):
    print("Installing ComfyUI")
    comfyui_commit = snapshot["comfyui"]
    if workspace.exists():
        if workspace.joinpath(".DONE").exists():
            commit = (workspace / ".DONE").read_text()
            if commit.strip() == comfyui_commit:
                print("ComfyUI is already installed")
                return
        shutil.rmtree(workspace)
    _clone_commit(COMFYUI_REPO, comfyui_commit, workspace, verbose=verbose)
    with open(workspace / ".DONE", "w") as f:
        f.write(comfyui_commit)


def install_custom_modules(snapshot, workspace: Path, verbose: int = 0):
    print("Installing custom nodes")
    for module in snapshot["custom_nodes"]:
        url = module["url"]
        directory = url.split("/")[-1].split(".")[0]
        module_dir = workspace / "custom_nodes" / directory

        if module_dir.exists():
            if module_dir.joinpath(".DONE").exists():
                commit = (module_dir / ".DONE").read_text()
                if commit.strip() == module["commit_hash"]:
                    print(f"{directory} is already installed")
                    continue
            shutil.rmtree(module_dir)

        commit_hash = module["commit_hash"]
        _clone_commit(url, commit_hash, module_dir, verbose=verbose)

        if module_dir.joinpath("install.py").exists():
            venv = workspace / ".venv"
            if venv.exists():
                python = (
                    venv / "Scripts" / "python.exe"
                    if os.name == "nt"
                    else venv / "bin" / "python"
                )
            else:
                python = Path(sys.executable)
            subprocess.check_call(
                [str(python.absolute()), "install.py"],
                cwd=module_dir,
                stdout=subprocess.DEVNULL if verbose == 0 else None,
            )

        with open(module_dir / ".DONE", "w") as f:
            f.write(commit_hash)


def install_dependencies(
    snapshot: dict,
    req_file: str,
    workspace: Path,
    verbose: int = 0,
):
    if verbose > 0:
        print("Installing Python dependencies")
    python_version = snapshot["python"]
    stdout = None if verbose > 0 else subprocess.DEVNULL
    stderr = None if verbose > 1 else subprocess.DEVNULL

    subprocess.check_call(
        ["uv", "python", "install", python_version],
        cwd=workspace,
        stdout=stdout,
        stderr=stderr,
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
        stdout=stdout,
        stderr=stderr,
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
        stdout=stdout,
        stderr=stderr,
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
        stdout=stdout,
        stderr=stderr,
    )
    with open(venv / "DONE", "w") as f:
        f.write("DONE")
    return venv_py


def install(cpack: str | Path, workspace: str | Path = "workspace", verbose: int = 0):
    workspace = Path(workspace)
    with tempfile.TemporaryDirectory() as temp_dir:
        pack_dir = Path(temp_dir) / ".cpack"
        shutil.unpack_archive(cpack, pack_dir)
        snapshot = json.loads((pack_dir / "snapshot.json").read_text())
        req_txt_file = pack_dir / "requirements.txt"

        install_comfyui(snapshot, workspace, verbose=verbose)
        install_dependencies(snapshot, str(req_txt_file), workspace, verbose=verbose)
        install_custom_modules(snapshot, workspace, verbose=verbose)

        for f in (pack_dir / "input").glob("*"):
            shutil.copy(f, workspace / "input" / f.name)
