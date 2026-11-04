from pathlib import Path

from stk.components.mise.mise import MISE
from stk.engine.component import Component
from stk.helpers.mise import install_mise_tools

FILES = Path(__file__).resolve().parent / "files"


def apply_uv() -> None:
    install_mise_tools("uv", FILES / "mise.toml")


UV = Component("uv", apply_uv, depends_on=(MISE,))
