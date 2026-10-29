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
    stdout: str = ""
    stderr: str = ""
    ignored_error_output: str | None = None


@dataclass(frozen=True)
class RunFailure:
    failed_operation: OperationDescription | None
    message: str
    captured_log_lines: Sequence[str]


class ComponentOutcome(Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
    NOT_APPLICABLE = "not applicable"


@dataclass(frozen=True)
class ComponentPlan:
    component_name: str
    operations: Sequence[PlannedOperation]
    planning_error: str | None
    not_applicable_reason: str | None = None


@dataclass(frozen=True)
class ComponentResult:
    component_name: str
    outcome: ComponentOutcome
    operation_results: Sequence[OperationResult]
    duration_seconds: float
    log_lines: Sequence[str] = ()
    failure: RunFailure | None = None
    skipped_because: str | None = None


class Reporter(Protocol):
    def run_started(self, component_names: Sequence[str]) -> None: ...

    def plan(
        self, component_plans: Sequence[ComponentPlan], visible: bool, /
    ) -> None: ...

    def confirm(self) -> bool: ...

    def component_started(self, component_name: str, /) -> None: ...

    def operation_started(self, description: OperationDescription, /) -> None: ...

    def operation_finished(self, result: OperationResult) -> None: ...

    def component_finished(self, result: ComponentResult) -> None: ...

    def run_finished(
        self, results: Sequence[ComponentResult], duration_seconds: float
    ) -> None: ...

    def close(self) -> None: ...
