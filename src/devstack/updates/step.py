from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Protocol

from devstack.component import Requirement, first_unmet_requirement


class StepOutcome(Enum):
    UPDATED = auto()
    DECLINED = auto()


class CommandFailedError(RuntimeError):
    def __init__(self, command: Sequence[str], exit_code: int) -> None:
        super().__init__(f"{' '.join(command)} exited with status {exit_code}")


class UpdateContext(Protocol):
    @property
    def assume_yes(self) -> bool: ...

    @property
    def bump_versions(self) -> bool: ...

    def section(self, title: str, /) -> None: ...

    def confirm(self, question: str, /) -> bool: ...

    def run(
        self,
        command: Sequence[str],
        *,
        working_directory: Path | None = None,
        environment: Mapping[str, str] | None = None,
    ) -> None: ...


@dataclass(frozen=True)
class UpdateStep:
    name: str
    run: Callable[[UpdateContext], StepOutcome]
    requires: tuple[Requirement, ...] = ()

    def unmet_requirement(self) -> Requirement | None:
        return first_unmet_requirement(self.requires)
