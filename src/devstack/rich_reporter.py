import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console, ConsoleOptions, Group, RenderResult
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Confirm
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from devstack.reporting import (
    ComponentOutcome,
    ComponentPlan,
    ComponentResult,
    OperationDescription,
    OperationResult,
    PlannedChange,
)

SYMBOL_UNCHANGED = "✔"
SYMBOL_CHANGED = "✱"
SYMBOL_FAILED = "✘"
SYMBOL_SKIPPED = "⤼"
SYMBOL_WARNING = "!"

PYINFRA_COMMAND_COUNT_PREFIX = "Error: executed"

PLAN_MARKERS = {
    PlannedChange.WILL_CHANGE: ("~", "yellow"),
    PlannedChange.CONDITIONAL: ("?", "dim"),
    PlannedChange.UNCHANGED: (" ", "dim"),
}


def format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f} s"
    minutes, remaining = divmod(int(seconds), 60)
    return f"{minutes} m {remaining:02d} s"


@dataclass
class RunningComponent:
    name: str
    started_at: float
    current_operation: str = ""
    spinner: Spinner = field(default_factory=lambda: Spinner("dots", style="cyan"))


class RichReporter:
    _console: Console
    _verbosity: int
    _log_path: Path | None
    _name_width: int
    _total_components: int
    _finished_count: int
    _running: dict[str, RunningComponent]
    _operations: dict[str, list[OperationResult]]
    _live: Live | None
    _run_started_at: float

    def __init__(
        self, console: Console, verbosity: int, log_path: Path | None = None
    ) -> None:
        self._console = console
        self._verbosity = verbosity
        self._log_path = log_path
        self._name_width = 0
        self._total_components = 0
        self._finished_count = 0
        self._running = {}
        self._operations = {}
        self._live = None
        self._run_started_at = time.monotonic()

    def run_started(self, component_names: Sequence[str]) -> None:
        self._name_width = max((len(name) for name in component_names), default=0)
        self._total_components = len(component_names)
        self._run_started_at = time.monotonic()

    def plan(self, component_plans: Sequence[ComponentPlan], visible: bool) -> None:
        if not visible:
            return
        tree = Tree("Plan", guide_style="dim")
        counts = {change: 0 for change in PlannedChange}
        for component_plan in component_plans:
            shown = [
                planned
                for planned in component_plan.operations
                if planned.change is not PlannedChange.UNCHANGED or self._verbosity >= 1
            ]
            for planned in component_plan.operations:
                counts[planned.change] += 1
            if not shown and component_plan.planning_error is None:
                continue
            branch = tree.add(Text(component_plan.component_name, style="bold"))
            if component_plan.planning_error is not None:
                branch.add(
                    Text(f"! could not plan: {component_plan.planning_error}", "red")
                )
            for planned in shown:
                marker, style = PLAN_MARKERS[planned.change]
                operation_name = self._shorten(planned.description.operation_name)
                branch.add(Text(f"{marker} {operation_name}", style))
        self._console.print(tree)
        self._console.print(
            Text(
                f"{counts[PlannedChange.WILL_CHANGE]} to change · "
                + f"{counts[PlannedChange.CONDITIONAL]} conditional · "
                + f"{counts[PlannedChange.UNCHANGED]} unchanged",
                style="dim",
            )
        )

    def confirm(self) -> bool:
        return Confirm.ask("Apply?", console=self._console, default=False)

    def component_started(self, component_name: str) -> None:
        self._running[component_name] = RunningComponent(
            component_name, time.monotonic()
        )
        self._operations[component_name] = []
        if self._live is None and self._console.is_terminal:
            self._live = Live(
                self, console=self._console, refresh_per_second=10, transient=True
            )
            self._live.start()

    def operation_started(self, description: OperationDescription) -> None:
        running = self._running.get(description.component_name)
        if running is not None:
            running.current_operation = description.operation_name

    def operation_finished(self, result: OperationResult) -> None:
        self._operations.setdefault(result.description.component_name, []).append(
            result
        )

    def component_finished(self, result: ComponentResult) -> None:
        self._running.pop(result.component_name, None)
        self._finished_count += 1
        operations = self._operations.pop(result.component_name, [])
        name = result.component_name
        duration = format_duration(result.duration_seconds)

        if result.outcome is ComponentOutcome.SKIPPED:
            detail = f"skipped ({result.skipped_because})"
            self._console.print(self._status_line(SYMBOL_SKIPPED, "dim", name, detail))
            return

        if result.outcome is ComponentOutcome.FAILED and result.failure is not None:
            self._console.print(
                self._status_line(SYMBOL_FAILED, "bold red", name, duration)
            )
            self._print_operations(operations)
            self._console.print(self._failure_panel(result))
            return

        changed = [operation for operation in operations if operation.changed]
        has_warning = any(op.ignored_error_output is not None for op in operations)
        if not changed and not has_warning and self._verbosity < 1:
            return
        symbol, style = (
            (SYMBOL_CHANGED, "yellow") if changed else (SYMBOL_UNCHANGED, "green")
        )
        self._console.print(self._status_line(symbol, style, name, duration))
        self._print_operations(operations)

    def run_finished(
        self, results: Sequence[ComponentResult], duration_seconds: float
    ) -> None:
        self._stop_live()
        operations = [op for result in results for op in result.operation_results]
        changed_count = sum(operation.changed for operation in operations)
        failed = [r for r in results if r.outcome is ComponentOutcome.FAILED]
        skipped = [r for r in results if r.outcome is ComponentOutcome.SKIPPED]
        warning_count = sum(op.ignored_error_output is not None for op in operations)
        timing = format_duration(duration_seconds)

        if not failed and not skipped and not warning_count and not changed_count:
            self._console.print(
                Text(
                    f"{SYMBOL_UNCHANGED} {len(results)} components up to date"
                    + f" · {len(operations)} operations · {timing}",
                    style="green",
                )
            )
            return

        parts = [Text(f"{SYMBOL_CHANGED} {changed_count} changed", "yellow")]
        if failed:
            parts.append(Text(f"{SYMBOL_FAILED} {len(failed)} failed", "bold red"))
        if skipped:
            parts.append(Text(f"{SYMBOL_SKIPPED} {len(skipped)} skipped", "dim"))
        if warning_count:
            parts.append(Text(f"{SYMBOL_WARNING} {warning_count} warnings", "yellow"))
        parts.append(Text(timing, "dim"))
        self._console.print()
        self._console.print(Text(" · ").join(parts))
        for result in failed:
            self._console.print(self._failure_summary_line(result))
        if (failed or warning_count) and self._log_path is not None:
            self._console.print(Text(f"  full log: {self._log_path}", style="dim"))

    def close(self) -> None:
        self._stop_live()

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        table = Table.grid(padding=(0, 1))
        now = time.monotonic()
        for running in self._running.values():
            table.add_row(
                running.spinner,
                Text(running.name.ljust(self._name_width), style="bold"),
                Text(
                    self._shorten(running.current_operation),
                    style="dim",
                    overflow="ellipsis",
                    no_wrap=True,
                ),
                Text(format_duration(now - running.started_at), style="dim"),
            )
        footer = Text(
            f"{self._finished_count}/{self._total_components} components"
            + f" · {format_duration(now - self._run_started_at)}",
            style="dim",
        )
        yield Group(table, footer)

    def _stop_live(self) -> None:
        if self._live is not None:
            self._live.stop()
            self._live = None

    def _status_line(self, symbol: str, style: str, name: str, detail: str) -> Text:
        return Text.assemble(
            (f"{symbol} ", style),
            (name.ljust(self._name_width), "bold"),
            ("  ", ""),
            (detail, "dim"),
        )

    def _print_operations(self, operations: Sequence[OperationResult]) -> None:
        for operation in operations:
            name = self._shorten(operation.description.operation_name)
            if operation.ignored_error_output is not None:
                self._console.print(
                    Text(f"    {SYMBOL_WARNING} {name} (error ignored)", style="yellow")
                )
                for line in operation.ignored_error_output.splitlines():
                    self._console.print(Text(f"        {line}", style="dim"))
            elif operation.changed or self._verbosity >= 1:
                symbol, style = (
                    (SYMBOL_CHANGED, "yellow")
                    if operation.changed
                    else (SYMBOL_UNCHANGED, "dim")
                )
                duration = format_duration(operation.duration_seconds)
                self._console.print(
                    Text(f"    {symbol} {name} ({duration})", style=style)
                )
            if self._verbosity >= 2:
                for line in (operation.stdout + "\n" + operation.stderr).splitlines():
                    if line.strip():
                        self._console.print(Text(f"        {line}", style="dim"))

    def _failure_panel(self, result: ComponentResult) -> Panel:
        failure = result.failure
        assert failure is not None
        operation_name = (
            failure.failed_operation.operation_name if failure.failed_operation else ""
        )
        lines = [Text(failure.message, style="bold")]
        lines.extend(Text(line) for line in failure.captured_log_lines)
        return Panel(
            Group(*lines),
            title=Text(f"{result.component_name} · {operation_name}", style="bold red"),
            title_align="left",
            border_style="red",
        )

    def _failure_summary_line(self, result: ComponentResult) -> Text:
        failure = result.failure
        operation_name = (
            failure.failed_operation.operation_name
            if failure is not None and failure.failed_operation is not None
            else "preparing"
        )
        detail = ""
        if failure is not None:
            output_lines = [
                line
                for line in failure.captured_log_lines
                if not line.startswith(PYINFRA_COMMAND_COUNT_PREFIX)
            ]
            detail = f" — {output_lines[-1] if output_lines else failure.message}"
        return Text(f"  {result.component_name}: {operation_name}{detail}", style="red")

    def _shorten(self, text: str) -> str:
        return text.replace(str(Path.home()), "~")
