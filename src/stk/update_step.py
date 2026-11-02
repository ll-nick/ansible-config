from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Protocol

from stk.requirement import Requirement, first_unmet_requirement


class StepOutcome(Enum):
    UPDATED = auto()
    SKIPPED = auto()


class CommandFailedError(RuntimeError):
    def __init__(self, command: Sequence[str], exit_code: int) -> None:
        super().__init__(f"{' '.join(command)} exited with status {exit_code}")


class UpdateContext(Protocol):
    @property
    def bump_versions(self) -> bool: ...

    @property
    def may_use_sudo(self) -> bool: ...

    def section(self, title: str, /) -> None: ...

    def confirm(self, question: str, /) -> bool: ...

    def note(self, message: str, /) -> None: ...

    def succeeds(
        self, command: Sequence[str], *, working_directory: Path | None = None
    ) -> bool: ...

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
    uses_sudo: bool = False

    def unmet_requirement(self) -> Requirement | None:
        return first_unmet_requirement(self.requires)
