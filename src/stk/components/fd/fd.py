from pathlib import Path

from stk.components.mise.mise import MISE
from stk.engine.component import Component
from stk.helpers.mise import install_mise_tools

FILES = Path(__file__).resolve().parent / "files"


def apply_fd() -> None:
    install_mise_tools("fd", FILES / "mise.toml")


FD = Component("fd", apply_fd, depends_on=(MISE,))
