from pathlib import Path

from devstack.mise import install_mise_tools
from devstack.pyinfra_adapters import component_deploy
from devstack.shells import add_bash_snippet, add_nushell_snippet

FILES = Path(__file__).resolve().parent / "files"


@component_deploy("eza")
def apply_eza() -> None:
    install_mise_tools("eza", FILES / "mise.toml")
    add_bash_snippet(FILES / "eza.bash")
    add_nushell_snippet(FILES / "eza.nu")
