from pathlib import Path

from stk.mise import install_mise_tools
from stk.pyinfra_adapters import component_deploy

FILES = Path(__file__).resolve().parent / "files"


@component_deploy("uv")
def apply_uv() -> None:
    install_mise_tools("uv", FILES / "mise.toml")
