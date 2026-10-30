from dataclasses import dataclass, field

from devstack.component import Requirement


@dataclass(frozen=True)
class RunSettings:
    privileged: bool = False
    sudo_password: str | None = field(default=None, repr=False)


_current_settings = RunSettings()


def configure_run_settings(settings: RunSettings) -> None:
    global _current_settings
    _current_settings = settings


def run_settings() -> RunSettings:
    return _current_settings


PRIVILEGED = Requirement(
    "privileged mode (--privileged)", lambda: run_settings().privileged
)
