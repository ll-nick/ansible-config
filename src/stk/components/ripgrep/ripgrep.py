from pathlib import Path

from stk.engine.pyinfra_adapters import component_deploy
from stk.helpers.mise import install_mise_tools

FILES = Path(__file__).resolve().parent / "files"


@component_deploy("ripgrep")
def apply_ripgrep() -> None:
    install_mise_tools("ripgrep", FILES / "mise.toml")
