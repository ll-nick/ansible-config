import sys
from collections.abc import Sequence
from typing import TextIO

from devstack.reporting import (
    OperationResult,
    PlannedChange,
    PlannedOperation,
    RunFailure,
)

CHANGE_MARKERS = {
    PlannedChange.WILL_CHANGE: "~",
    PlannedChange.CONDITIONAL: "?",
    PlannedChange.UNCHANGED: " ",
}


class PlainReporter:
    _verbosity: int
    _output: TextIO
    _current_component_name: str | None

    def __init__(self, verbosity: int, output: TextIO = sys.stdout) -> None:
        self._verbosity = verbosity
        self._output = output
        self._current_component_name = None

    def plan(self, planned_operations: Sequence[PlannedOperation]) -> None:
        will_change_count = 0
        conditional_count = 0
        unchanged_count = 0
        current_component_name: str | None = None
        for planned in planned_operations:
            if planned.change is PlannedChange.WILL_CHANGE:
                will_change_count += 1
            elif planned.change is PlannedChange.CONDITIONAL:
                conditional_count += 1
            else:
                unchanged_count += 1
            if planned.change is PlannedChange.UNCHANGED and self._verbosity < 1:
                continue
            if planned.description.component_name != current_component_name:
                current_component_name = planned.description.component_name
                self._print(current_component_name)
            marker = CHANGE_MARKERS[planned.change]
            self._print(f"  {marker} {planned.description.operation_name}")
        self._print(
            f"Plan: {will_change_count} to change, {conditional_count} conditional,"
            + f" {unchanged_count} unchanged"
        )

    def confirm(self) -> bool:
        return input("Apply? [y/N] ").strip().lower() in {"y", "yes"}

    def operation_finished(self, result: OperationResult) -> None:
        if not result.changed and self._verbosity < 1:
            return
        component_name = result.description.component_name
        if component_name != self._current_component_name:
            self._current_component_name = component_name
            self._print(component_name)
        marker = "*" if result.changed else "="
        operation_name = result.description.operation_name
        self._print(f"  {marker} {operation_name} ({result.duration_seconds:.1f}s)")

    def run_failed(self, failure: RunFailure) -> None:
        if failure.failed_operation is not None:
            description = failure.failed_operation
            self._print(
                f"FAILED: {description.component_name} | {description.operation_name}"
            )
        else:
            self._print("FAILED")
        self._print(failure.message)
        for line in failure.captured_log_lines:
            self._print(f"  {line}")

    def run_finished(
        self, results: Sequence[OperationResult], duration_seconds: float
    ) -> None:
        changed_count = sum(result.changed for result in results)
        if changed_count == 0:
            operation_count = len(results)
            self._print(
                f"Everything up to date ({operation_count} operations,"
                + f" {duration_seconds:.1f}s)"
            )
            return
        unchanged_count = len(results) - changed_count
        self._print(
            f"Done: {changed_count} changed, {unchanged_count} unchanged"
            + f" ({duration_seconds:.1f}s)"
        )

    def _print(self, message: str) -> None:
        print(message, file=self._output)
