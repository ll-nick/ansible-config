from pathlib import Path

from devstack.file_copy import EXECUTABLE_MODE, copy_file
from devstack.machine import has_display, has_systemd
from devstack.pyinfra_adapters import component_deploy
from devstack.systemd import USER_UNIT_DIRECTORY, enable_user_unit

FILES = Path(__file__).resolve().parent / "files"


@component_deploy("stk")
def apply_stk() -> None:
    copy_file(FILES / "stk", Path.home() / ".local/bin/stk", mode=EXECUTABLE_MODE)

    if has_display() and has_systemd():
        copy_file(
            FILES / "stk-check.service", USER_UNIT_DIRECTORY / "stk-check.service"
        )
        copy_file(FILES / "stk-check.timer", USER_UNIT_DIRECTORY / "stk-check.timer")
        enable_user_unit("stk-check.timer")
