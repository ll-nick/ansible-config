import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

from devstack.reporting import (
    ComponentOutcome,
    ComponentPlan,
    ComponentResult,
    OperationDescription,
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
    _name_width: int
    _log_path: Path | None

    def __init__(
        self,
        verbosity: int,
        output: TextIO | None = None,
        log_path: Path | None = None,
    ) -> None:
        self._verbosity = verbosity
        self._output = output if output is not None else sys.stdout
        self._name_width = 0
        self._log_path = log_path

    def run_started(self, component_names: Sequence[str]) -> None:
        self._name_width = max((len(name) for name in component_names), default=0)

    def plan(self, component_plans: Sequence[ComponentPlan], visible: bool) -> None:
        if not visible:
            return
        will_change_count = 0
        conditional_count = 0
        unchanged_count = 0
        for component_plan in component_plans:
            lines: list[str] = []
            if component_plan.not_applicable_reason is not None:
                continue
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

    def component_started(self, _component_name: str) -> None:
        pass

    def operation_started(self, _description: OperationDescription) -> None:
        pass

    def operation_finished(self, result: OperationResult) -> None:
        component_name = result.description.component_name
        operation_name = result.description.operation_name
        if result.ignored_error_output is not None:
            self._print_line(component_name, f"! {operation_name} (error ignored)")
            for line in result.ignored_error_output.splitlines():
                self._print_line(component_name, f"    {line}")
            return
        if not result.changed and self._verbosity < 1:
            return
        marker = "*" if result.changed else "="
        self._print_line(
            component_name,
            f"{marker} {operation_name} ({result.duration_seconds:.1f}s)",
        )

    def component_finished(self, result: ComponentResult) -> None:
        name = result.component_name
        if result.outcome is ComponentOutcome.SKIPPED:
            self._print_line(name, f"- skipped ({result.skipped_because})")
            return
        if result.outcome is ComponentOutcome.NOT_APPLICABLE:
            if self._verbosity >= 1:
                self._print_line(name, f"- not applicable ({result.skipped_because})")
            return
        if result.outcome is not ComponentOutcome.FAILED or result.failure is None:
            return
        failure = result.failure
        if failure.failed_operation is not None:
            failed_name = failure.failed_operation.operation_name
            self._print_line(name, f"! FAILED: {failed_name}")
        else:
            self._print_line(name, "! FAILED")
        self._print_line(name, f"    {failure.message}")
        for line in failure.captured_log_lines:
            self._print_line(name, f"      {line}")

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
        if (failed_names or ignored_error_count) and self._log_path is not None:
            self._print(f"Full log: {self._log_path}")
        if changed_count == 0 and not failed_names and not ignored_error_count:
            self._print(
                f"Everything up to date ({len(operation_results)} operations, {timing})"
            )
            return
        unchanged_count = len(operation_results) - changed_count
        self._print(
            f"Done: {changed_count} changed, {unchanged_count} unchanged ({timing})"
        )

    def close(self) -> None:
        pass

    def _print_line(self, component_name: str, message: str) -> None:
        self._print(f"{component_name:<{self._name_width}}  {message}")

    def _print(self, message: str) -> None:
        print(message, file=self._output)


def _names_with_outcome(
    results: Sequence[ComponentResult], outcome: ComponentOutcome
) -> list[str]:
    return [result.component_name for result in results if result.outcome is outcome]
