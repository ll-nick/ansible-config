from pathlib import Path

from stk.components.bash.bash import BASH
from stk.components.mise.mise import MISE
from stk.components.nushell.nushell import NUSHELL
from stk.engine.component import Component
from stk.helpers.mise import install_mise_tools
from stk.helpers.shells import add_bash_snippet, add_nushell_snippet

FILES = Path(__file__).resolve().parent / "files"


def apply_fzf() -> None:
    install_mise_tools("fzf", FILES / "mise.toml")
    add_bash_snippet(FILES / "fzf.bash")
    add_nushell_snippet(FILES / "fzf.nu")


FZF = Component("fzf", apply_fzf, depends_on=(MISE, BASH, NUSHELL))
