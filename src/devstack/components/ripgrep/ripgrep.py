from pathlib import Path

from devstack.mise import install_mise_tools
from devstack.pyinfra_adapters import component_deploy

FILES = Path(__file__).resolve().parent / "files"


@component_deploy("ripgrep")
def apply_ripgrep() -> None:
    install_mise_tools("ripgrep", FILES / "mise.toml")
