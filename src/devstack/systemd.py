from pathlib import Path

from pyinfra.operations import systemd

USER_UNIT_DIRECTORY = Path.home() / ".config" / "systemd" / "user"


# pyinfra accepts running=None to leave the current state alone,
# which matters because stopping the tmux unit would kill every session
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
