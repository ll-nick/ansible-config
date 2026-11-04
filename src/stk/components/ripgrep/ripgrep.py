from pathlib import Path

from stk.components.mise.mise import MISE
from stk.engine.component import Component
from stk.helpers.mise import install_mise_tools

FILES = Path(__file__).resolve().parent / "files"


def apply_ripgrep() -> None:
    install_mise_tools("ripgrep", FILES / "mise.toml")


RIPGREP = Component("ripgrep", apply_ripgrep, depends_on=(MISE,))
