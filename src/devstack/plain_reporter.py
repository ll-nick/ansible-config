import sys
from collections.abc import Sequence
from typing import TextIO

from devstack.reporting import (
    ComponentOutcome,
    ComponentPlan,
    ComponentResult,
    OperationResult,
    PlannedChange,
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
    _header_printed: bool

    def __init__(self, verbosity: int, output: TextIO = sys.stdout) -> None:
        self._verbosity = verbosity
        self._output = output
        self._current_component_name = None
        self._header_printed = False

    def plan(self, component_plans: Sequence[ComponentPlan]) -> None:
        will_change_count = 0
        conditional_count = 0
        unchanged_count = 0
        for component_plan in component_plans:
            lines: list[str] = []
            if component_plan.planning_error is not None:
                lines.append(f"  ! could not plan: {component_plan.planning_error}")
            for planned in component_plan.operations:
                if planned.change is PlannedChange.WILL_CHANGE:
                    will_change_count += 1
                elif planned.change is PlannedChange.CONDITIONAL:
                    conditional_count += 1
                else:
                    unchanged_count += 1
                    if self._verbosity < 1:
                        continue
                marker = CHANGE_MARKERS[planned.change]
                lines.append(f"  {marker} {planned.description.operation_name}")
            if lines:
                self._print(component_plan.component_name)
                for line in lines:
                    self._print(line)
        self._print(
            f"Plan: {will_change_count} to change, {conditional_count} conditional,"
            + f" {unchanged_count} unchanged"
        )

    def confirm(self) -> bool:
        return input("Apply? [y/N] ").strip().lower() in {"y", "yes"}

    def component_started(self, component_name: str) -> None:
        self._current_component_name = component_name
        self._header_printed = False

    def operation_finished(self, result: OperationResult) -> None:
        operation_name = result.description.operation_name
        if result.ignored_error_output is not None:
            self._print_header_once()
            self._print(f"  ! {operation_name} (error ignored)")
            for line in result.ignored_error_output.splitlines():
                self._print(f"      {line}")
            return
        if not result.changed and self._verbosity < 1:
            return
        self._print_header_once()
        marker = "*" if result.changed else "="
        self._print(f"  {marker} {operation_name} ({result.duration_seconds:.1f}s)")

    def component_finished(self, result: ComponentResult) -> None:
        if result.outcome is ComponentOutcome.SKIPPED:
            self._print(f"{result.component_name}: skipped ({result.skipped_because})")
            return
        if result.outcome is not ComponentOutcome.FAILED or result.failure is None:
            return
        self._print_header_once()
        failure = result.failure
        if failure.failed_operation is not None:
            self._print(f"  ! FAILED: {failure.failed_operation.operation_name}")
        else:
            self._print("  ! FAILED")
        self._print(f"    {failure.message}")
        for line in failure.captured_log_lines:
            self._print(f"      {line}")

    def run_finished(
        self, results: Sequence[ComponentResult], duration_seconds: float
    ) -> None:
        operation_results = [
            operation for result in results for operation in result.operation_results
        ]
        changed_count = sum(operation.changed for operation in operation_results)
        failed_names = _names_with_outcome(results, ComponentOutcome.FAILED)
        skipped_names = _names_with_outcome(results, ComponentOutcome.SKIPPED)
        if failed_names:
            self._print(f"Failed: {', '.join(failed_names)}")
        if skipped_names:
            self._print(f"Skipped: {', '.join(skipped_names)}")
        ignored_error_count = sum(
            operation.ignored_error_output is not None
            for operation in operation_results
        )
        timing = f"{duration_seconds:.1f}s"
        if ignored_error_count:
            self._print(f"Warnings: {ignored_error_count} ignored errors")
        if changed_count == 0 and not failed_names and not ignored_error_count:
            self._print(
                f"Everything up to date ({len(operation_results)} operations, {timing})"
            )
            return
        unchanged_count = len(operation_results) - changed_count
        self._print(
            f"Done: {changed_count} changed, {unchanged_count} unchanged ({timing})"
        )

    def _print_header_once(self) -> None:
        if not self._header_printed and self._current_component_name is not None:
            self._header_printed = True
            self._print(self._current_component_name)

    def _print(self, message: str) -> None:
        print(message, file=self._output)


def _names_with_outcome(
    results: Sequence[ComponentResult], outcome: ComponentOutcome
) -> list[str]:
    return [result.component_name for result in results if result.outcome is outcome]
