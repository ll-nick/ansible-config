from pathlib import Path

from stk.engine.pyinfra_adapters import component_deploy
from stk.helpers.links import symlink_file
from stk.helpers.mise import install_mise_tools
from stk.helpers.shells import add_bash_snippet, add_nushell_snippet

FILES = Path(__file__).resolve().parent / "files"


@component_deploy("lazygit")
def apply_lazygit() -> None:
    install_mise_tools("lazygit", FILES / "mise.toml")
    symlink_file(FILES / "config.yml", Path.home() / ".config/lazygit/config.yml")
    add_bash_snippet(FILES / "lazygit.bash")
    add_nushell_snippet(FILES / "lazygit.nu")
