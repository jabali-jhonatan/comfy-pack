import click


@click.group()
def main():
    """ComfyUI IDL CLI"""


@main.command(name="install")
@click.option(
    "--workspace",
    "-w",
    default="workspace",
    help="Workspace directory",
    type=click.Path(file_okay=False),
)
@click.argument("cpack", type=click.Path(exists=True, dir_okay=False))
def install_cmd(cpack: str, workspace: str):
    """
    Install ComfyUI workspace from a zipped package.

    Example:

        # Install to the default directory(`workspace`)

        $ comfyui_idl install workspace.cpack.zip

        # Install to a different directory

        $ comfyui_idl install -w my_workspace workspace.cpack.zip
    """
    from .package import install

    install(cpack, workspace)
