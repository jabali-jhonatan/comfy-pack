from __future__ import annotations

import copy
import subprocess
import tempfile
import logging
import os
import json
from pathlib import Path
from typing import Any, Union
from comfyui_idl.utils import (
    populate_workflow_inputs_outputs,
    retrieve_workflow_outputs,
)

logger = logging.getLogger(__name__)


class WorkflowRunner:
    def __init__(self, workspace: str, output_dir: str, temp_dir: str):
        self.workspace = workspace
        self.output_dir = output_dir
        self.temp_dir = temp_dir

        # The ComfyUI process
        self.is_running = False

    def start(self):
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
            logger.info("Successfully started ComfyUI in the background")
        else:
            logger.error("Failed to start ComfyUI in the background")

    def stop(self):
        if not self.is_running:
            raise RuntimeError("ComfyUI Runner is not started yet")

        logger.info("Stopping ComfyUI...")
        command = ["comfy", "stop"]
        subprocess.run(command, check=True)
        logger.info("Successfully stopped ComfyUI")

        self.is_running = False

    def run_workflow(
        self,
        workflow: dict,
        temp_dir: Union[str, Path, None] = None,
        timeout: int = 300,
        **kwargs: Any,
    ) -> Any:
        if not self.is_running:
            raise RuntimeError("ComfyUI Runner is not started yet")

        workflow_copy = copy.deepcopy(workflow)
        if temp_dir is None:
            temp_dir = Path(tempfile.mkdtemp())
        if isinstance(temp_dir, str):
            temp_dir = Path(temp_dir)

        populate_workflow_inputs_outputs(
            workflow_copy,
            temp_dir,
            **kwargs,
        )

        workflow_file_path = temp_dir / "workflow.json"
        with open(workflow_file_path, "w") as file:
            json.dump(workflow_copy, file)

        # Execute the workflow
        command = [
            "comfy",
            "run",
            "--workflow",
            workflow_file_path.as_posix(),
            "--timeout",
            str(timeout),
            "--wait",
        ]
        subprocess.run(command, check=True)

        # retrieve the output
        return retrieve_workflow_outputs(
            workflow_copy,
            temp_dir,
        )
