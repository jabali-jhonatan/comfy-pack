import click
import hashlib
import functools
import json
from pathlib import Path
import shutil
import tempfile


@click.group()
@click.option(
    "--verbose",
    "-v",
    count=True,
    help="Increase verbosity level (use multiple times for more verbosity)",
)
@click.pass_context
def main(ctx, verbose):
    """ComfyUI IDL CLI"""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


@main.command(name="unpack")
@click.argument("cpack", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--output",
    "-o",
    default="ComfyUI",
    help="target directory to unpack the ComfyUI project",
    type=click.Path(file_okay=False),
)
@click.pass_context
def unpack_cmd(ctx, cpack: str, workspace: str):
    """
    Install ComfyUI workspace from a zipped package.

    Example:

        # Install to the default directory(`workspace`)

        $ comfyui_idl install workspace.cpack.zip

        # Install to a different directory

        $ comfyui_idl install -w my_workspace workspace.cpack.zip
    """
    from .package import install

    install(cpack, workspace, ctx.obj["verbose"])


def _print_schema(schema, verbose: int = 0):
    from rich.table import Table
    from rich.console import Console

    table = Table(title="")

    # Add columns
    table.add_column("Input", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Required", style="yellow")
    table.add_column("Default", style="blue")
    table.add_column("Range", style="magenta")

    # Get required fields
    required = schema.get("required", [])

    # Add rows
    for field, info in schema["properties"].items():
        range_str = ""
        if "minimum" in info or "maximum" in info:
            min_val = info.get("minimum", "")
            max_val = info.get("maximum", "")
            range_str = f"{min_val} to {max_val}"

        table.add_row(
            field,
            info.get("format", "") or info.get("type", ""),
            "✓" if field in required else "",
            str(info.get("default", "")),
            range_str,
        )

    Console().print(table)


@main.command(name="info")
@click.argument("cpack", type=click.Path(exists=True, dir_okay=False))
@click.pass_context
def info_cmd(ctx, cpack: str):
    """
    Display information about the ComfyUI package.

    Example:
        $ comfyui_idl info workspace.cpack.zip
    """
    from .utils import generate_input_model

    with tempfile.TemporaryDirectory() as temp_dir:
        pack_dir = Path(temp_dir) / ".cpack"
        shutil.unpack_archive(cpack, pack_dir)
        workflow = json.loads((pack_dir / "workflow_api.json").read_text())

    inputs = generate_input_model(workflow)
    _print_schema(inputs.model_json_schema(), ctx.obj["verbose"])


@functools.lru_cache
def _get_cache_workspace(cpack: str):
    m = hashlib.sha256()
    with open(cpack, "rb") as f:
        m.update(f.read())
    return Path.home() / ".comfypack" / "workspace" / m.hexdigest()[0:8]


@main.command(
    context_settings={
        "ignore_unknown_options": True,
        "allow_extra_args": True,
    },
)
@click.argument("cpack", type=click.Path(exists=True, dir_okay=False))
@click.option("--output-dir", "-o", type=click.Path(), default=".")
@click.pass_context
def run(ctx, cpack: str, output_dir: str):
    from .utils import generate_input_model
    from pydantic import ValidationError
    from rich.console import Console

    inputs = dict(
        zip([k.lstrip("-").replace("-", "_") for k in ctx.args[::2]], ctx.args[1::2])
    )

    console = Console()

    with tempfile.TemporaryDirectory() as temp_dir:
        pack_dir = Path(temp_dir) / ".cpack"
        shutil.unpack_archive(cpack, pack_dir)
        workflow = json.loads((pack_dir / "workflow_api.json").read_text())

    input_model = generate_input_model(workflow)

    try:
        validated_data = input_model(**inputs)
        console.print("[green]✓ Input is valid![/green]")
        for field, value in validated_data.model_dump().items():
            console.print(f"{field}: {value}")
    except ValidationError as e:
        console.print("[red]✗ Validation failed![/red]")
        for error in e.errors():
            console.print(f"- {error['loc'][0]}: {error['msg']}")
        return 1

    from .package import install

    workspace = _get_cache_workspace(cpack)
    if not (workspace / "DONE").exists():
        if workspace.exists():
            shutil.rmtree(workspace)
        install(cpack, workspace)
        with open(workspace / "DONE", "w") as f:
            f.write("DONE")
    console.print(f"\n[green]✓ ComfyUI Workspace is retrieved![/green]")
    console.print(f"Workspace: {workspace}")

    from .run import WorkflowRunner

    runner = None
    try:
        runner = WorkflowRunner(str(workspace.absolute()))
        runner.start()
        console.print("\n[green]✓ ComfyUI is launched in the background![/green]")
        runner.run_workflow(
            workflow,
            Path(output_dir).absolute(),
            verbose=ctx.obj["verbose"],
            **validated_data.model_dump(),
        )
        console.print("\n[green]✓ Workflow is executed successfully![/green]")
        console.print(f"Output is saved to {Path(output_dir).absolute()}")
    finally:
        if runner:
            runner.stop(verbose=ctx.obj["verbose"])
