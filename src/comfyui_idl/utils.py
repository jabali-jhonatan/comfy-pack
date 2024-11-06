from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic import BaseModel

CLASS_TYPES = {
    "BentoInputString": str,
    "BentoInputBoolean": bool,
    "BentoInputInteger": int,
    "BentoInputFloat": float,
    "BentoInputPath": Path,
    "BentoInputImage": Path,
}

BENTO_OUTPUT_NODE = "BentoOutputPath"


def _get_node_value(node: dict) -> any:
    return next(iter(node["inputs"].values()))


def _set_node_value(node: dict, value: any) -> None:
    key = next(iter(node["inputs"].keys()))
    if isinstance(value, Path):
        value = value.as_posix()
    node["inputs"][key] = value


def _normalize_to_identifier(s: str) -> str:
    if not s:
        return "_"

    s = re.sub(r"[^a-zA-Z0-9_]", "_", s)

    if s[0].isdigit():
        s = "_" + s

    s = re.sub(r"_+", "_", s)
    s = s.strip("_")
    s = s if s else "_"
    return s.lower()


def _get_input_name(node, dep_map) -> str:
    """
    Get the input name from the node
    """
    title = node["_meta"]["title"]
    if title.isidentifier():
        return title
    nid = node["id"]
    if (nid, 0) in dep_map:
        return list(dep_map[(nid, 0)]["inputs"].keys())[0]
    return _normalize_to_identifier(title)


def _get_output_name(node) -> str:
    title = node["_meta"]["title"]
    if title.isidentifier():
        return title
    return _normalize_to_identifier(title)


def _parse_workflow(workflow: dict) -> tuple[dict, dict]:
    """
    Parse the workflow template and return the input and output definition
    """
    inputs = {}
    outputs = {}
    dep_map = {}

    for id, node in workflow.items():
        for i in node["inputs"].values():
            if isinstance(i, list) and len(i) == 2:  # is a link
                dep_map[tuple(i)] = id

    for id, node in workflow.items():
        node["id"] = id
        if node["class_type"].startswith("BentoInput"):
            name = _get_input_name(node, dep_map)
            if name in inputs:
                name = f"{name}_{id}"
            inputs[name] = node
        elif node["class_type"].startswith("BentoOutput"):
            name = _get_output_name(node)
            if name in inputs:
                name = f"{name}_{id}"
            outputs[name] = node

    return inputs, outputs


def generate_input_model(workflow: dict) -> type[BaseModel]:
    """
    Generate a pydantic model from the input definition
    """

    from pydantic import Field, create_model

    inputs, _ = _parse_workflow(workflow)

    input_fields = {}
    for name, node in inputs.items():
        class_type = node["class_type"]
        if class_type in CLASS_TYPES:
            ann = CLASS_TYPES[class_type]
            if class_type != "BentoInputPath":
                field = (ann, Field(default=_get_node_value(node)))
            else:
                field = (ann, Field())
            input_fields[name] = field
        else:
            raise ValueError(f"Unsupported class type: {class_type}")
    return create_model("ParsedWorkflowTemplate", **input_fields)


def populate_workflow_inputs_outputs(
    workflow: dict, output_path: Path, **kwargs
) -> dict:
    """
    Fill the input values and output path into the workflow
    """
    input_spec, output_spec = _parse_workflow(workflow)
    for k, v in kwargs.items():
        node = input_spec[k]
        if not node["class_type"].startswith("BentoInput"):
            raise ValueError(f"Node {k} is not an input node")
        _set_node_value(workflow[node["id"]], v)

    for _, node in output_spec.items():
        node_id = node["id"]
        if node["class_type"] == BENTO_OUTPUT_NODE:
            workflow[node_id]["inputs"]["filename_prefix"] = (
                output_path / f"{node_id}_"
            ).as_posix()
    return workflow


def retrieve_workflow_outputs(workflow: dict, output_path: Path) -> Path:
    """
    Get the output file by name from the workflow
    """
    _, outputs = _parse_workflow(workflow)
    if len(outputs) != 1:
        raise ValueError("Multiple output nodes are not supported")
    node = list(outputs.values())[0]
    if node["class_type"] != BENTO_OUTPUT_NODE:
        raise ValueError(f"Output node is not of type {BENTO_OUTPUT_NODE}")
    node_id = node["id"]
    return next(output_path.glob(f"{node_id}_*"))
