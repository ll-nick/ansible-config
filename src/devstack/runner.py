import logging
import time
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from pyinfra.api.connect import connect_all
from pyinfra.api.exceptions import PyinfraError
from pyinfra.api.operations import run_ops
from pyinfra.api.state import BaseStateCallback, State

from devstack.component import Component
from devstack.pyinfra_adapters import (
    create_local_state,
    operation_order,
    prepare_component,
)
from devstack.reporting import (
    OperationDescription,
    OperationResult,
    PlannedChange,
    PlannedOperation,
    Reporter,
    RunFailure,
)
from pyinfra import logger as pyinfra_logger

EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_CHANGES_DETECTED = 3


@dataclass(frozen=True)
class RunOptions:
    dry_run: bool
    assume_yes: bool
    fail_on_change: bool


class LogCapture(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.INFO)
        self.lines: list[str] = []

    @override
    def emit(self, record: logging.LogRecord) -> None:
        self.lines.append(record.getMessage())


class ReportingCallbacks(BaseStateCallback):
    _reporter: Reporter

    def __init__(self, reporter: Reporter) -> None:
        self._reporter = reporter
        self._operation_started_at: dict[str, float] = {}
        self.results: list[OperationResult] = []
        self.current_operation: OperationDescription | None = None

    @override
    def operation_start(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, state: State, op_hash: str
    ) -> None:
        self._operation_started_at[op_hash] = time.monotonic()
        self.current_operation = describe_operation(state, op_hash)

    @override
    def operation_end(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, state: State, op_hash: str
    ) -> None:
        duration_seconds = time.monotonic() - self._operation_started_at[op_hash]
        changed = any(
            state.get_op_data_for_host(host, op_hash).operation_meta.did_change()
            for host in state.inventory.get_active_hosts()
        )
        result = OperationResult(
            description=describe_operation(state, op_hash),
            changed=changed,
            duration_seconds=duration_seconds,
        )
        self.results.append(result)
        self._reporter.operation_finished(result)


def describe_operation(state: State, op_hash: str) -> OperationDescription:
    pyinfra_name = sorted(state.get_op_meta(op_hash).names)[0]
    return OperationDescription.from_pyinfra_name(pyinfra_name)


def collect_plan(state: State) -> list[PlannedOperation]:
    planned_operations: list[PlannedOperation] = []
    for op_hash in operation_order(state):
        change = PlannedChange.UNCHANGED
        for host in state.inventory.get_active_hosts():
            operation_data = state.get_op_data_for_host(host, op_hash)
            if not operation_data.operation_meta.will_change:
                continue
            if operation_data.global_arguments["_if"]:
                change = PlannedChange.CONDITIONAL
            else:
                change = PlannedChange.WILL_CHANGE
        planned_operations.append(
            PlannedOperation(describe_operation(state, op_hash), change)
        )
    return planned_operations


def run_components(
    components: Sequence[Component], options: RunOptions, reporter: Reporter
) -> int:
    log_capture = LogCapture()
    pyinfra_logger.addHandler(log_capture)
    pyinfra_logger.setLevel(logging.INFO)

    callbacks = ReportingCallbacks(reporter)
    state = create_local_state(callbacks)

    started_at = time.monotonic()
    try:
        connect_all(state)
        for component in components:
            prepare_component(state, component.apply)

        planned_operations = collect_plan(state)
        reporter.plan(planned_operations)
        if options.dry_run:
            return EXIT_SUCCESS
        has_pending_changes = any(
            planned.change is not PlannedChange.UNCHANGED
            for planned in planned_operations
        )
        if has_pending_changes and not options.assume_yes and not reporter.confirm():
            return EXIT_FAILURE

        run_ops(state)
    except PyinfraError as error:
        reporter.run_failed(
            RunFailure(callbacks.current_operation, str(error), log_capture.lines)
        )
        return EXIT_FAILURE

    reporter.run_finished(callbacks.results, time.monotonic() - started_at)
    if options.fail_on_change and any(result.changed for result in callbacks.results):
        return EXIT_CHANGES_DETECTED
    return EXIT_SUCCESS
