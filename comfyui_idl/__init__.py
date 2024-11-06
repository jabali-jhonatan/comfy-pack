from typing import TYPE_CHECKING
import copy


if TYPE_CHECKING:
    from pydantic import BaseModel
    from pathlib import Path


def parse_workflow(workflow: dict) -> tuple[dict, dict]:
    """
    Parse the workflow template and return the input and output definition
    """
    inputs = {}
    outputs = {}

    for id, node in workflow.items():
        if node["class_type"].startswith("BentoInput"):
            name = node["_meta"]["title"]
            node["id"] = id
            inputs[name] = node
        elif node["class_type"].startswith("BentoOutput"):
            name = node["_meta"]["title"]
            node["id"] = id
            outputs[name] = node

    return inputs, outputs


def generate_input_model(inputs: dict) -> type[BaseModel]:
    """
    Generate a pydantic model from the input definition
    """
    from pydantic import create_model, Field
    from pathlib import Path

    input_fields = {}
    for name, node in inputs.items():
        if node["class_type"] == "BentoInputPath":
            input_fields[name] = (Path, Field())
    return create_model("ParsedWorkflowTemplate", **input_fields)


def populate_workflow_inputs(workflow: dict, **kwargs) -> dict:
    """
    Fill the input values into the workflow
    """
    input_spec, _ = parse_workflow(workflow)
    workflow_copy = copy.deepcopy(workflow)
    for k, v in kwargs.items():
        node = input_spec[k]
        if node["class_type"] == "BentoInputPath":
            workflow_copy[node["id"]]["inputs"]["path"] = v
    return workflow_copy


def configure_workflow_outputs(workflow: dict, output_path: Path) -> dict:
    """
    Configure the output path for the workflow
    """
    _, outputs = parse_workflow(workflow)
    workflow_copy = copy.deepcopy(workflow)
    for _, node in outputs.items():
        node_id = node["id"]
        if node["class_type"] == "BentoOutputPath":
            workflow_copy[node["id"]]["inputs"]["filename_prefix"] = (
                output_path / f"{node_id}_"
            ).as_posix()
    return workflow_copy


def retrieve_workflow_output(workflow: dict, output_path: Path) -> Path:
    """
    Get the output file by name from the workflow
    """
    _, outputs = parse_workflow(workflow)
    if len(outputs) == 1:
        node = list(outputs.values())[0]
        node_id = node["id"]
        return output_path.glob(f"{node_id}_*").__next__()
    assert False, "Multiple output nodes are not supported"
