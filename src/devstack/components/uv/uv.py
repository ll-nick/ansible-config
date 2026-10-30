from pathlib import Path

from devstack.mise import install_mise_tools
from devstack.pyinfra_adapters import component_deploy

FILES = Path(__file__).resolve().parent / "files"


@component_deploy("uv")
def apply_uv() -> None:
    install_mise_tools("uv", FILES / "mise.toml")
