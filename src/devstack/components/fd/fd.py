from pathlib import Path

from devstack.mise import install_mise_tools
from devstack.pyinfra_adapters import component_deploy

FILES = Path(__file__).resolve().parent / "files"


@component_deploy("fd")
def apply_fd() -> None:
    install_mise_tools("fd", FILES / "mise.toml")
