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
    url = 'http://127.0.0.1:8188/api/customnode/getmappings'
    params = {'mode': 'nickname'}
    full_url = f"{url}?{parse.urlencode(params)}"
    req = request.Request(full_url)
    _ = request.urlopen(req)


class WorkflowRunner:
    """
    A class to manage and run ComfyUI workflows.

    This class handles the initialization, starting, stopping, and execution of ComfyUI workflows.
    It manages temporary and output directories, and provides methods to run workflows with specified parameters.

    Attributes:
        temp_dir (Path): The temporary directory for ComfyUI operations.
        output_dir (Path): The output directory for ComfyUI results.
        workspace (str): The workspace path for ComfyUI.
        is_running (bool): Flag indicating whether ComfyUI is currently running.
    """

    def __init__(
        self,
        workspace: str,
        temp_dir: Union[str, Path, None] = None,
        output_dir: Union[str, Path, None] = None,
    ) -> None:
        """
        Initialize the WorkflowRunner.

        Args:
            workspace (str): The workspace path for ComfyUI.
            temp_dir (Union[str, Path, None], optional): The temporary directory. Defaults to None.
            output_dir (Union[str, Path, None], optional): The output directory. Defaults to None.
        """
        if temp_dir is None:
            self.temp_dir = Path(tempfile.mkdtemp())
            self._cleanup_temp_dir = True
        elif isinstance(temp_dir, str):
            self.temp_dir = Path(temp_dir)
            self._cleanup_temp_dir = False
        else:
            self.temp_dir = temp_dir
            self._cleanup_temp_dir = False

        if output_dir is None:
            self.output_dir = self.temp_dir
        elif isinstance(output_dir, str):
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = output_dir

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
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
        print("Comfy Output Path:", self.output_dir)
        print("Comfy Temp Path:", self.temp_dir)

        logger.info("Starting ComfyUI in the background...")
        command = [
            "comfy",
            "--workspace",
            self.workspace,
            "launch",
            "--background",
            "--",
            "--output-directory",
            self.output_dir,
            "--temp-directory",
            self.temp_dir,
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
        if self._cleanup_temp_dir:
            logger.info("Cleaning up temporary directory...")
            shutil.rmtree(self.temp_dir)
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
            temp_dir = self.temp_dir
        if isinstance(temp_dir, str):
            temp_dir = Path(temp_dir)

        populate_workflow(
            workflow_copy,
            temp_dir,
            **kwargs,
        )

        workflow_file_path = temp_dir / "workflow.json"
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
