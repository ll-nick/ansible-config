from pathlib import Path

from stk.components.bash.bash import BASH
from stk.components.mise.mise import MISE
from stk.components.nushell.nushell import NUSHELL
from stk.engine.component import Component
from stk.helpers.mise import install_mise_tools
from stk.helpers.shells import add_bash_snippet, add_nushell_snippet

FILES = Path(__file__).resolve().parent / "files"


def apply_eza() -> None:
    install_mise_tools("eza", FILES / "mise.toml")
    add_bash_snippet(FILES / "eza.bash")
    add_nushell_snippet(FILES / "eza.nu")


EZA = Component("eza", apply_eza, depends_on=(MISE, BASH, NUSHELL))
