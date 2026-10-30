import shlex
from dataclasses import dataclass

from gevent import subprocess

from devstack.commands import run_command


@dataclass(frozen=True)
class DconfSetting:
    key: str
    value: str


def read_dconf_value(key: str) -> str | None:
    try:
        completed = subprocess.run(
            ["dconf", "read", key], capture_output=True, text=True, check=True
        )
    except OSError, subprocess.CalledProcessError:
        return None
    return completed.stdout.strip() or None


def apply_dconf_settings(settings: list[DconfSetting]) -> None:
    for setting in settings:
        if read_dconf_value(setting.key) == setting.value:
            continue
        run_command(
            f"Set dconf {setting.key}",
            f"dconf write {shlex.quote(setting.key)} {shlex.quote(setting.value)}",
        )


def reset_dconf_key(key: str) -> None:
    if read_dconf_value(key) is None:
        return
    run_command(f"Reset dconf {key}", f"dconf reset {shlex.quote(key)}")
