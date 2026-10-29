from functools import cache
from pathlib import Path

from pyinfra.operations import files, server

from devstack.file_copy import copy_file

MISE_INSTALL_SCRIPT_URL = "https://mise.jdx.dev/install.sh"


def mise_executable() -> Path:
    return Path.home() / ".local" / "bin" / "mise"


def mise_config_directory() -> Path:
    return Path.home() / ".config" / "mise" / "conf.d"


@cache
def ensure_mise_installed() -> None:
    files.directory(
        name="Ensure ~/.local/bin exists",
        path=str(mise_executable().parent),
    )
    server.shell(
        name="Install mise",
        commands=[f"curl -fsSL {MISE_INSTALL_SCRIPT_URL} | sh"],
        _if=lambda: not mise_executable().exists(),
    )


def install_mise_tools(component_name: str, mise_config_source: Path) -> None:
    ensure_mise_installed()
    config_upload = copy_file(
        mise_config_source, mise_config_directory() / f"{component_name}.toml"
    )
    server.shell(
        name=f"Install mise tools for {component_name}",
        commands=[f"{mise_executable()} install"],
        _if=[config_upload.did_change],
    )
