from pathlib import Path

from stk.engine.component import Component
from stk.helpers.links import symlink_file
from stk.helpers.mise import install_mise_tools
from stk.helpers.shells import add_bash_snippet, add_nushell_snippet
from stk_config.components.bash.bash import BASH
from stk_config.components.mise.mise import MISE
from stk_config.components.nushell.nushell import NUSHELL

FILES = Path(__file__).resolve().parent / "files"


def apply_lazygit() -> None:
    install_mise_tools("lazygit", FILES / "mise.toml")
    symlink_file(FILES / "config.yml", Path.home() / ".config/lazygit/config.yml")
    add_bash_snippet(FILES / "lazygit.bash")
    add_nushell_snippet(FILES / "lazygit.nu")


LAZYGIT = Component("lazygit", apply_lazygit, depends_on=(MISE, BASH, NUSHELL))
