from pathlib import Path

from devstack.mise import install_mise_tools

FILES = Path(__file__).resolve().parent / "files"

install_mise_tools("fd", FILES / "mise.toml")
