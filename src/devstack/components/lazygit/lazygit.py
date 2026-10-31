from pathlib import Path

from devstack.links import link_repository_file
from devstack.mise import install_mise_tools
from devstack.pyinfra_adapters import component_deploy
from devstack.shells import add_bash_snippet, add_nushell_snippet

FILES = Path(__file__).resolve().parent / "files"


@component_deploy("lazygit")
def apply_lazygit() -> None:
    install_mise_tools("lazygit", FILES / "mise.toml")
    link_repository_file(
        FILES / "config.yml", Path.home() / ".config/lazygit/config.yml"
    )
    add_bash_snippet(FILES / "lazygit.bash")
    add_nushell_snippet(FILES / "lazygit.nu")
