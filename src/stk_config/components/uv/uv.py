from pathlib import Path

from stk.engine.component import Component
from stk.helpers.mise import install_mise_tools
from stk_config.components.mise.mise import MISE

FILES = Path(__file__).resolve().parent / "files"


def apply_uv() -> None:
    install_mise_tools("uv", FILES / "mise.toml")


UV = Component("uv", apply_uv, depends_on=(MISE,))
