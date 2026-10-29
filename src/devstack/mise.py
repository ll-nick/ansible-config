from pathlib import Path

from devstack.commands import run_command
from devstack.file_copy import copy_file

MISE_INSTALL_SCRIPT_URL = "https://mise.jdx.dev/install.sh"


def mise_executable() -> Path:
    return Path.home() / ".local" / "bin" / "mise"


def mise_config_directory() -> Path:
    return Path.home() / ".config" / "mise" / "conf.d"


def install_mise_tools(component_name: str, mise_config_source: Path) -> None:
    config_upload = copy_file(
        mise_config_source, mise_config_directory() / f"{component_name}.toml"
    )
    run_command(
        f"Install mise tools for {component_name}",
        f"{mise_executable()} install",
        when_any_changed=[config_upload],
    )
