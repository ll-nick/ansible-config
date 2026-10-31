import os
import re
import shutil
import socket
from pathlib import Path

from gevent import subprocess

from devstack.component import Requirement

OS_RELEASE_PATH = Path("/etc/os-release")
SYSTEMD_RUNTIME_DIRECTORY = Path("/run/systemd/system")
LOCAL_DISPLAY_PATTERN = re.compile(r":[0-9]")
VERSION_PATTERN = re.compile(r"\d+(?:\.\d+)*")
JOY_HOSTNAME = "mrtjoy"


def has_display() -> bool:
    local_x_display = LOCAL_DISPLAY_PATTERN.match(os.environ.get("DISPLAY", ""))
    return local_x_display is not None or bool(os.environ.get("WAYLAND_DISPLAY"))


def hostname() -> str:
    return socket.gethostname()


def has_inkscape() -> bool:
    return shutil.which("inkscape") is not None


def has_systemd() -> bool:
    return SYSTEMD_RUNTIME_DIRECTORY.is_dir()


def parse_os_release(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        key, separator, value = line.partition("=")
        if separator and not line.startswith("#"):
            fields[key.strip()] = value.strip().strip("\"'")
    return fields


def distribution_ids() -> frozenset[str]:
    try:
        fields = parse_os_release(OS_RELEASE_PATH.read_text())
    except OSError:
        return frozenset()
    identifiers = {fields.get("ID", "")}
    identifiers.update(fields.get("ID_LIKE", "").split())
    identifiers.discard("")
    return frozenset(identifiers)


def parse_version(text: str) -> tuple[int, ...] | None:
    match = VERSION_PATTERN.search(text)
    if match is None:
        return None
    return tuple(int(part) for part in match.group().split("."))


def git_version() -> tuple[int, ...] | None:
    try:
        completed = subprocess.run(
            ["git", "--version"], capture_output=True, text=True, check=True
        )
    except OSError, subprocess.CalledProcessError:
        return None
    return parse_version(completed.stdout)


HAS_DISPLAY = Requirement("a display", has_display)
HAS_INKSCAPE = Requirement("inkscape", has_inkscape)


def runs_distribution(*identifiers: str) -> Requirement:
    wanted = frozenset(identifiers)
    return Requirement(
        f"distribution {' or '.join(identifiers)}",
        lambda: bool(wanted & distribution_ids()),
    )


def does_not_run_distribution(identifier: str) -> Requirement:
    return Requirement(
        f"a distribution other than {identifier}",
        lambda: identifier not in distribution_ids(),
    )


def host_is(name: str) -> Requirement:
    return Requirement(f"the host {name}", lambda: hostname() == name)
