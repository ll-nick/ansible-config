from pathlib import Path

from pyinfra.operations import files, systemd

from stk.machine import has_systemd

USER_UNIT_DIRECTORY = Path.home() / ".config" / "systemd" / "user"


def install_user_unit_file(source: Path) -> None:
    files.put(
        name=f"Install systemd user unit {source.name}",
        src=str(source),
        dest=str(USER_UNIT_DIRECTORY / source.name),
        mode="644",
    )


# pyinfra accepts running=None to leave the current state alone,
# as stopping a unit ends whatever runs in it
def enable_user_unit(unit_name: str) -> None:
    systemd.service(
        name=f"Enable systemd user unit {unit_name}",
        service=unit_name,
        running=None,  # pyright: ignore[reportArgumentType]
        enabled=True,
        user_mode=True,
    )


def disable_user_unit(unit_name: str) -> None:
    systemd.service(
        name=f"Disable systemd user unit {unit_name}",
        service=unit_name,
        running=None,  # pyright: ignore[reportArgumentType]
        enabled=False,
        user_mode=True,
    )


def remove_user_unit(unit_name: str) -> None:
    """Removes a unit that is no longer installed, leaving what it runs alone."""
    unit_file = USER_UNIT_DIRECTORY / f"{unit_name}.service"
    if not unit_file.exists():
        return
    if has_systemd():
        disable_user_unit(unit_name)
    files.file(
        name=f"Remove systemd user unit {unit_file.name}",
        path=str(unit_file),
        present=False,
    )
    if has_systemd():
        systemd.daemon_reload(name="Reload systemd user units", user_mode=True)
