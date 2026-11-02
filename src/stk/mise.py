import tomllib
from pathlib import Path
from typing import cast

from gevent import subprocess

from stk.commands import run_command
from stk.json_settings import parse_json_object
from stk.links import symlink_file
from stk.requirement import Requirement

MISE_INSTALL_SCRIPT_URL = "https://mise.jdx.dev/install.sh"
# mise aborts when a config changes while it reads them, and it reads the configs
# of all components, which other components may be linking at that moment
MISE_INSTALL_RETRIES = 3


def mise_executable() -> Path:
    return Path.home() / ".local" / "bin" / "mise"


MISE_IS_INSTALLED = Requirement("mise", lambda: mise_executable().exists())


def mise_config_directory() -> Path:
    return Path.home() / ".config" / "mise" / "conf.d"


def mise_exec(*command: str) -> list[str]:
    return [str(mise_executable()), "exec", "--", *command]


def missing_mise_tools() -> frozenset[str]:
    try:
        completed = subprocess.run(
            [str(mise_executable()), "ls", "--missing", "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
    except OSError, subprocess.CalledProcessError:
        return frozenset()
    return frozenset(parse_json_object(completed.stdout))


def declared_mise_tools(mise_config_source: Path) -> frozenset[str]:
    config = cast("dict[str, object]", tomllib.loads(mise_config_source.read_text()))
    return frozenset(cast("dict[str, object]", config.get("tools", {})))


def install_mise_tools(component_name: str, mise_config_source: Path) -> None:
    config_upload = symlink_file(
        mise_config_source, mise_config_directory() / f"{component_name}.toml"
    )
    # Also retries after an interrupted install, when the config is already in place
    tools_are_missing = bool(
        declared_mise_tools(mise_config_source) & missing_mise_tools()
    )
    run_command(
        f"Install mise tools for {component_name}",
        f"{mise_executable()} install",
        when_any_changed=() if tools_are_missing else [config_upload],
        retries=MISE_INSTALL_RETRIES,
    )
