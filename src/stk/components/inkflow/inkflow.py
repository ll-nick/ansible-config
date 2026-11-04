from pathlib import Path

from stk.components.bash.bash import BASH
from stk.components.mise.mise import MISE
from stk.components.neovim.neovim import NEOVIM
from stk.components.nushell.nushell import NUSHELL
from stk.engine.component import Component
from stk.helpers.links import symlink_file
from stk.helpers.mise import install_mise_tools
from stk.helpers.shells import add_bash_snippet, add_nushell_snippet
from stk.machine import HAS_DISPLAY, has_executable

FILES = Path(__file__).resolve().parent / "files"


def apply_inkflow() -> None:
    install_mise_tools("inkflow", FILES / "mise.toml")
    symlink_file(
        FILES / "inkflow-edit-svg", Path.home() / ".local/bin/inkflow-edit-svg"
    )
    add_bash_snippet(FILES / "inkflow.bash")
    add_nushell_snippet(FILES / "inkflow.nu")


INKFLOW = Component(
    "inkflow",
    apply_inkflow,
    depends_on=(MISE, BASH, NUSHELL, NEOVIM),
    requires=(HAS_DISPLAY, has_executable("inkscape")),
)
