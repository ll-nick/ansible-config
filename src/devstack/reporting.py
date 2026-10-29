from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

OPERATION_NAME_SEPARATOR = " | "


class PlannedChange(Enum):
    UNCHANGED = "unchanged"
    WILL_CHANGE = "will change"
    CONDITIONAL = "conditional"


@dataclass(frozen=True)
class OperationDescription:
    component_name: str
    operation_name: str

    @staticmethod
    def from_pyinfra_name(pyinfra_name: str) -> OperationDescription:
        component_name, separator, operation_name = pyinfra_name.partition(
            OPERATION_NAME_SEPARATOR
        )
        if not separator:
            return OperationDescription("", pyinfra_name)
        return OperationDescription(component_name, operation_name)


@dataclass(frozen=True)
class PlannedOperation:
    description: OperationDescription
    change: PlannedChange


@dataclass(frozen=True)
class OperationResult:
    description: OperationDescription
    changed: bool
    duration_seconds: float


@dataclass(frozen=True)
class RunFailure:
    failed_operation: OperationDescription | None
    message: str
    captured_log_lines: Sequence[str]


class Reporter(Protocol):
    def plan(self, planned_operations: Sequence[PlannedOperation]) -> None: ...

    def confirm(self) -> bool: ...

    def operation_finished(self, result: OperationResult) -> None: ...

    def run_failed(self, failure: RunFailure) -> None: ...

    def run_finished(
        self, results: Sequence[OperationResult], duration_seconds: float
    ) -> None: ...
