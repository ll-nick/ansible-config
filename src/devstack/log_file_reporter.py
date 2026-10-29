import os
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import TextIO

from devstack.reporting import (
    ComponentOutcome,
    ComponentPlan,
    ComponentResult,
    OperationDescription,
    OperationResult,
)

LOG_RETENTION_COUNT = 20
LAST_RUN_LINK_NAME = "last-run.log"


def state_directory() -> Path:
    state_home = os.environ.get("XDG_STATE_HOME")
    base = Path(state_home) if state_home else Path.home() / ".local" / "state"
    return base / "devstack"


class LogFileReporter:
    _runs_directory: Path
    log_path: Path
    _file: TextIO | None

    def __init__(self, directory: Path | None = None) -> None:
        self._runs_directory = (directory or state_directory()) / "runs"
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.log_path = self._runs_directory / f"{timestamp}.log"
        self._file = None

    def run_started(self, component_names: Sequence[str]) -> None:
        self._runs_directory.mkdir(parents=True, exist_ok=True)
        self._file = self.log_path.open("w", buffering=1)
        self._link_last_run()
        self._prune_old_logs()
        self._write(f"run started: {', '.join(component_names)}")

    def plan(self, component_plans: Sequence[ComponentPlan], _visible: bool) -> None:
        for component_plan in component_plans:
            if component_plan.planning_error is not None:
                self._write(
                    f"plan {component_plan.component_name}: "
                    + f"could not plan: {component_plan.planning_error}"
                )
            for planned in component_plan.operations:
                self._write(
                    f"plan {component_plan.component_name} | "
                    + f"{planned.description.operation_name}: {planned.change.value}"
                )

    def confirm(self) -> bool:
        return True

    def component_started(self, component_name: str) -> None:
        self._write(f"component started: {component_name}")

    def operation_started(self, description: OperationDescription) -> None:
        self._write(
            f"operation started: {description.component_name} | "
            + description.operation_name
        )

    def operation_finished(self, result: OperationResult) -> None:
        description = result.description
        status = "changed" if result.changed else "unchanged"
        if result.ignored_error_output is not None:
            status = "error ignored"
        self._write(
            f"operation finished: {description.component_name} | "
            + f"{description.operation_name}: {status} "
            + f"({result.duration_seconds:.2f}s)"
        )
        for label, output in (
            ("stdout", result.stdout),
            ("stderr", result.stderr),
            ("ignored error", result.ignored_error_output or ""),
        ):
            for line in output.splitlines():
                self._write(f"    {label}: {line}")

    def component_finished(self, result: ComponentResult) -> None:
        self._write(
            f"component finished: {result.component_name}: "
            + f"{result.outcome.value} ({result.duration_seconds:.2f}s)"
        )
        if result.outcome is ComponentOutcome.SKIPPED:
            self._write(f"    skipped because {result.skipped_because}")
        if result.failure is not None:
            self._write(f"    failure: {result.failure.message}")
        for line in result.log_lines:
            self._write(f"    pyinfra: {line}")
        if result.failure is not None:
            for line in result.failure.captured_log_lines:
                self._write(f"    failure log: {line}")

    def run_finished(
        self, results: Sequence[ComponentResult], duration_seconds: float
    ) -> None:
        outcome_counts = ", ".join(
            f"{sum(result.outcome is outcome for result in results)} {outcome.value}"
            for outcome in ComponentOutcome
        )
        self._write(f"run finished in {duration_seconds:.2f}s ({outcome_counts})")

    def close(self) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None

    def _write(self, message: str) -> None:
        if self._file is None:
            return
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self._file.write(f"{timestamp} {message}\n")

    def _link_last_run(self) -> None:
        link = self._runs_directory.parent / LAST_RUN_LINK_NAME
        temporary_link = link.with_name(f"{LAST_RUN_LINK_NAME}.tmp")
        temporary_link.unlink(missing_ok=True)
        temporary_link.symlink_to(self.log_path)
        temporary_link.replace(link)

    def _prune_old_logs(self) -> None:
        logs = sorted(self._runs_directory.glob("*.log"))
        for old_log in logs[:-LOG_RETENTION_COUNT]:
            old_log.unlink(missing_ok=True)
