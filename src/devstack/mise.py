from functools import cache
from pathlib import Path

from pyinfra.operations import files, server

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
    files.directory(
        name="Ensure mise conf.d exists",
        path=str(mise_config_directory()),
    )


def install_mise_tools(component_name: str, mise_config_source: Path) -> None:
    ensure_mise_installed()
    config_upload = files.put(
        name=f"Add mise config for {component_name}",
        src=str(mise_config_source),
        dest=str(mise_config_directory() / f"{component_name}.toml"),
        mode="644",
    )
    server.shell(
        name=f"Install mise tools for {component_name}",
        commands=[f"{mise_executable()} install"],
        _if=[config_upload.did_change],
    )
