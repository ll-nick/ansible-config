from pathlib import Path

from stk.mise import install_mise_tools
from stk.pyinfra_adapters import component_deploy

FILES = Path(__file__).resolve().parent / "files"


@component_deploy("ripgrep")
def apply_ripgrep() -> None:
    install_mise_tools("ripgrep", FILES / "mise.toml")
