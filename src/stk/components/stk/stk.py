from pathlib import Path

from stk.engine.component import Component
from stk.helpers.links import symlink_file
from stk.helpers.systemd import enable_user_unit, install_user_unit_file
from stk.machine import has_display, has_systemd

FILES = Path(__file__).resolve().parent / "files"


def apply_stk() -> None:
    symlink_file(FILES / "stk", Path.home() / ".local/bin/stk")

    if has_display() and has_systemd():
        install_user_unit_file(FILES / "stk-check.service")
        install_user_unit_file(FILES / "stk-check.timer")
        enable_user_unit("stk-check.timer")


STK = Component("stk", apply_stk)
