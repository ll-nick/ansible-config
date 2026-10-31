from pathlib import Path

from devstack.links import link_repository_file
from devstack.mise import install_mise_tools
from devstack.pyinfra_adapters import component_deploy
from devstack.shells import add_bash_snippet, add_nushell_snippet

FILES = Path(__file__).resolve().parent / "files"


@component_deploy("inkflow")
def apply_inkflow() -> None:
    install_mise_tools("inkflow", FILES / "mise.toml")
    link_repository_file(
        FILES / "inkflow-edit-svg", Path.home() / ".local/bin/inkflow-edit-svg"
    )
    add_bash_snippet(FILES / "inkflow.bash")
    add_nushell_snippet(FILES / "inkflow.nu")
