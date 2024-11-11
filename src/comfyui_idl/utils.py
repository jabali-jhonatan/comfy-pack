from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

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

BENTO_OUTPUT_NODES = {
    "BentoOutputPath",
    "BentoOutputImage",
}

BENTO_PATH_INPUT_NODES = {
    "BentoInputPath",
    "BentoInputImage",
}


def _get_node_value(node: dict) -> Any:
    return next(iter(node["inputs"].values()))


def _set_node_value(node: dict, value: Any) -> None:
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


def _get_node_identifier(node, dep_map=None) -> str:
    """
    Get the input name from the node
    """
    title = node["_meta"]["title"]
    if title.isidentifier():
        return title
    nid = node["id"]
    if dep_map and (nid, 0) in dep_map:
        _, input_name = dep_map[(nid, 0)]
        return _normalize_to_identifier(input_name)

    return _normalize_to_identifier(title)


def _parse_workflow(workflow: dict) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Parse the workflow template and return the input and output definition
    """
    inputs = {}
    outputs = {}
    dep_map = {}

    for id, node in workflow.items():
        for input_name, v in node["inputs"].items():
            if isinstance(v, list) and len(v) == 2:  # is a link
                dep_map[tuple(v)] = node, input_name

    for id, node in workflow.items():
        node["id"] = id
        if node["class_type"].startswith("BentoInput"):
            name = _get_node_identifier(node, dep_map)
            if name in inputs:
                name = f"{name}_{id}"
            inputs[name] = node
        elif node["class_type"].startswith("BentoOutput"):
            name = _get_node_identifier(node)
            if name in inputs:
                name = f"{name}_{id}"
            outputs[name] = node

    return inputs, outputs


def parse_workflow(workflow: dict) -> tuple[dict, dict]:
    """
    Describe the workflow template
    """
    return _parse_workflow(workflow)


def generate_input_model(workflow: dict) -> type[BaseModel]:
    """
    Generates a pydantic model from the input definition.

    Args:
        workflow (dict): The workflow template to generate the model from.

    Returns:
        type[BaseModel]: A pydantic model class representing the input definition.

    Raises:
        ValueError: If an unsupported class type is encountered in the workflow.
    """
    from pydantic import Field, create_model

    inputs, _ = _parse_workflow(workflow)

    input_fields = {}
    for name, node in inputs.items():
        class_type = node["class_type"]
        if class_type in CLASS_TYPES:
            ann = CLASS_TYPES[class_type]
            if class_type in BENTO_PATH_INPUT_NODES:
                field = (ann, Field())
            else:
                field = (ann, Field(default=_get_node_value(node)))
            input_fields[name] = field
        else:
            raise ValueError(f"Unsupported class type: {class_type}")
    return create_model("ParsedWorkflowTemplate", **input_fields)


def populate_workflow(workflow: dict, output_path: Path, **inputs) -> dict:
    """
    Fills the input values and output path into the workflow.

    Args:
        workflow (dict): The workflow template to populate.
        output_path (Path): The path where output files will be saved.
        **inputs: Keyword arguments representing input values for the workflow.

    Returns:
        dict: The populated workflow with input values and output paths set.

    Raises:
        ValueError: If a provided input key does not correspond to an input node.
    """
    input_spec, output_spec = _parse_workflow(workflow)
    for k, v in inputs.items():
        node = input_spec[k]
        if not node["class_type"].startswith("BentoInput"):
            raise ValueError(f"Node {k} is not an input node")
        _set_node_value(workflow[node["id"]], v)

    for _, node in output_spec.items():
        node_id = node["id"]
        if node["class_type"] in BENTO_OUTPUT_NODES:
            workflow[node_id]["inputs"]["filename_prefix"] = (
                output_path / f"{node_id}_"
            ).as_posix()
    return workflow


def retrieve_workflow_outputs(
    workflow: dict,
    output_path: Path,
) -> Union[Path, list[Path], dict[str, Path], dict[str, list[Path]]]:
    """
    Gets the output file(s) from the workflow.

    Args:
        workflow (dict): The workflow template to retrieve outputs from.
        output_path (Path): The path where output files are saved.

    Returns:
        Union[Path, list[Path], dict[str, Path], dict[str, list[Path]]]:
            - A single Path if there's only one output file.
            - A list of Paths if there are multiple files for a single output.
            - A dictionary mapping output names to Paths or lists of Paths for multiple outputs.

    Raises:
        ValueError: If the output node is not of the expected type.
    """
    _, outputs = _parse_workflow(workflow)
    if len(outputs) != 1:
        value_map = {}
        for k, node in outputs.items():
            node_id = node["id"]
            path_strs = list(output_path.glob(f"{node_id}_*"))
            if len(path_strs) == 1:
                value_map[k] = path_strs[0]
            else:
                value_map[k] = path_strs
        return value_map

    name, node = next(iter(outputs.items()))
    if node["class_type"] not in BENTO_OUTPUT_NODES:
        raise ValueError(f"Output node {name} is not of type {BENTO_OUTPUT_NODES}")
    node_id = node["id"]

    outs = list(output_path.glob(f"{node_id}_*"))
    if len(outs) == 1:
        return outs[0]
    return outs
