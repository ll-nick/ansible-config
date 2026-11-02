from pathlib import Path

from stk.mise import install_mise_tools
from stk.pyinfra_adapters import component_deploy

FILES = Path(__file__).resolve().parent / "files"


@component_deploy("fd")
def apply_fd() -> None:
    install_mise_tools("fd", FILES / "mise.toml")
