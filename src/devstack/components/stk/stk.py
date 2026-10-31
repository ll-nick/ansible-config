from pathlib import Path

from devstack.links import symlink_file
from devstack.machine import has_display, has_systemd
from devstack.pyinfra_adapters import component_deploy
from devstack.systemd import enable_user_unit, install_user_unit_file

FILES = Path(__file__).resolve().parent / "files"


@component_deploy("stk")
def apply_stk() -> None:
    symlink_file(FILES / "stk", Path.home() / ".local/bin/stk")

    if has_display() and has_systemd():
        install_user_unit_file(FILES / "stk-check.service")
        install_user_unit_file(FILES / "stk-check.timer")
        enable_user_unit("stk-check.timer")
