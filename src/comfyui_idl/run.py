from __future__ import annotations

import copy
import json
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Union

from comfyui_idl.utils import (
    populate_workflow,
    retrieve_workflow_outputs,
)

logger = logging.getLogger(__name__)


def _probe_comfyui_server():
    from urllib import parse, request

    url = "http://127.0.0.1:8188/api/customnode/getmappings"
    params = {"mode": "nickname"}
    full_url = f"{url}?{parse.urlencode(params)}"
    req = request.Request(full_url)
    _ = request.urlopen(req)


class WorkflowRunner:
    def __init__(
        self,
        workspace: str,
    ) -> None:
        """
        Initialize the WorkflowRunner.

        Args:
            workspace (str): The workspace path for ComfyUI.
        """
        self.workspace = workspace

        # The ComfyUI process
        self.is_running = False

    def start(self) -> None:
        """
        Start the ComfyUI process.

        This method starts ComfyUI in the background, sets up necessary directories,
        and disables tracking for workaround purposes.

        Raises:
            RuntimeError: If ComfyUI is already running.
        """
        if self.is_running:
            raise RuntimeError("ComfyUI Runner is already started")

        logger.info(
            "Disable tracking from Comfy CLI, not for privacy concerns, but to workaround a bug"
        )
        command = ["comfy", "--skip-prompt", "tracking", "disable"]
        subprocess.run(command, check=True)
        logger.info("Successfully disabled Comfy CLI tracking")

        logger.info("Preparing directories required by ComfyUI...")

        logger.info("Starting ComfyUI in the background...")
        command = [
            "comfy",
            "--workspace",
            self.workspace,
            "launch",
            "--background",
        ]
        if subprocess.run(command, check=True):
            self.is_running = True
            _probe_comfyui_server()
            logger.info("Successfully started ComfyUI in the background")
        else:
            logger.error("Failed to start ComfyUI in the background")

    def stop(self) -> None:
        """
        Stop the ComfyUI process.

        This method stops the running ComfyUI process and cleans up the temporary directory if necessary.

        Raises:
            RuntimeError: If ComfyUI is not currently running.
        """
        if not self.is_running:
            raise RuntimeError("ComfyUI Runner is not started yet")

        logger.info("Stopping ComfyUI...")
        command = ["comfy", "stop"]
        subprocess.run(command, check=True)
        logger.info("Successfully stopped ComfyUI")

        logger.info("Cleaning up temporary directory...")
        shutil.rmtree(Path(self.workspace) / "output", ignore_errors=True)
        # shutil.rmtree(Path(self.workspace) / "temp", ignore_errors=True)
        shutil.rmtree(Path(self.workspace) / "worflow.json", ignore_errors=True)
        logger.info("Successfully cleaned up temporary directory")

        self.is_running = False

    def run_workflow(
        self,
        workflow: dict,
        temp_dir: Union[str, Path, None] = None,
        timeout: int = 300,
        **kwargs: Any,
    ) -> Any:
        """
        Run a ComfyUI workflow.

        This method executes a given workflow, populates it with input data,
        and retrieves the output.

        Args:
            workflow (dict): The workflow to run.
            temp_dir (Union[str, Path, None], optional): Temporary directory for the workflow. Defaults to None.
            timeout (int, optional): Timeout for the workflow execution in seconds. Defaults to 300.
            **kwargs: Additional keyword arguments for workflow population.

        Returns:
            Any: The output of the workflow.

        Raises:
            RuntimeError: If ComfyUI is not started.
        """
        if not self.is_running:
            raise RuntimeError("ComfyUI Runner is not started yet")

        workflow_copy = copy.deepcopy(workflow)
        if temp_dir is None:
            temp_dir = Path(".")
        if isinstance(temp_dir, str):
            temp_dir = Path(temp_dir)

        populate_workflow(
            workflow_copy,
            temp_dir,
            **kwargs,
        )

        workflow_file_path = Path(self.workspace) / "workflow.json"
        with open(workflow_file_path, "w") as file:
            json.dump(workflow_copy, file)

        extra_args = []
        if "BENTOML_DEBUG" in os.environ:
            extra_args.append("--verbose")

        # Execute the workflow
        command = [
            "comfy",
            "run",
            "--workflow",
            workflow_file_path.as_posix(),
            "--timeout",
            str(timeout),
            "--wait",
            *extra_args,
        ]
        subprocess.run(command, check=True)

        # retrieve the output
        return retrieve_workflow_outputs(
            workflow_copy,
            temp_dir,
        )
