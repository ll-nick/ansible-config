import logging
import time
import traceback
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
    ComponentOutcome,
    ComponentPlan,
    ComponentResult,
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
    lines: list[str]

    def __init__(self) -> None:
        super().__init__(level=logging.WARNING)
        self.lines = []

    @override
    def emit(self, record: logging.LogRecord) -> None:
        self.lines.append(record.getMessage())


class ReportingCallbacks(BaseStateCallback):
    _reporter: Reporter
    _operation_started_at: dict[str, float]
    results: list[OperationResult]
    current_operation: OperationDescription | None

    def __init__(self, reporter: Reporter) -> None:
        self._reporter = reporter
        self._operation_started_at = {}
        self.results = []
        self.current_operation = None

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
            ignored_error_output=ignored_error_output(state, op_hash),
        )
        self.results.append(result)
        self._reporter.operation_finished(result)


def describe_operation(state: State, op_hash: str) -> OperationDescription:
    pyinfra_name = sorted(state.get_op_meta(op_hash).names)[0]
    return OperationDescription.from_pyinfra_name(pyinfra_name)


def ignored_error_output(state: State, op_hash: str) -> str | None:
    for host in state.inventory.get_active_hosts():
        operation_meta = state.get_op_data_for_host(host, op_hash).operation_meta
        if operation_meta.did_error():
            return operation_meta.stderr.strip() or operation_meta.stdout.strip()
    return None


def describe_error(error: Exception) -> str:
    return f"{type(error).__name__}: {error}"


def prepare_state(component: Component, callbacks: BaseStateCallback) -> State:
    state = create_local_state(callbacks)
    connect_all(state)
    prepare_component(state, component.apply)
    return state


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


def plan_component(component: Component) -> ComponentPlan:
    try:
        state = prepare_state(component, BaseStateCallback())
    except Exception as error:
        return ComponentPlan(component.name, (), describe_error(error))
    return ComponentPlan(component.name, tuple(collect_plan(state)), None)


def execute_component(
    component: Component, reporter: Reporter, log_capture: LogCapture
) -> ComponentResult:
    callbacks = ReportingCallbacks(reporter)
    log_capture.lines.clear()
    started_at = time.monotonic()
    reporter.component_started(component.name)
    try:
        state = prepare_state(component, callbacks)
        run_ops(state)
    except Exception as error:
        captured_lines = list(log_capture.lines)
        if not isinstance(error, PyinfraError):
            captured_lines.extend(traceback.format_exc().splitlines())
        failure = RunFailure(
            callbacks.current_operation, describe_error(error), captured_lines
        )
        return ComponentResult(
            component.name,
            ComponentOutcome.FAILED,
            callbacks.results,
            time.monotonic() - started_at,
            failure=failure,
        )
    return ComponentResult(
        component.name,
        ComponentOutcome.SUCCEEDED,
        callbacks.results,
        time.monotonic() - started_at,
    )


def skipped_result(
    component: Component, unsuccessful_dependency: str
) -> ComponentResult:
    return ComponentResult(
        component.name,
        ComponentOutcome.SKIPPED,
        (),
        0.0,
        skipped_because=f"dependency {unsuccessful_dependency} did not succeed",
    )


def has_pending_changes(component_plans: Sequence[ComponentPlan]) -> bool:
    return any(
        component_plan.planning_error is not None
        or any(
            planned.change is PlannedChange.WILL_CHANGE
            for planned in component_plan.operations
        )
        for component_plan in component_plans
    )


def run_components(
    components: Sequence[Component], options: RunOptions, reporter: Reporter
) -> int:
    log_capture = LogCapture()
    pyinfra_logger.addHandler(log_capture)
    pyinfra_logger.setLevel(logging.INFO)

    started_at = time.monotonic()
    component_plans = [plan_component(component) for component in components]
    reporter.plan(component_plans)
    if options.dry_run:
        return EXIT_SUCCESS
    if (
        has_pending_changes(component_plans)
        and not options.assume_yes
        and not reporter.confirm()
    ):
        return EXIT_FAILURE

    results: list[ComponentResult] = []
    unsuccessful_names: set[str] = set()
    for component in components:
        unsuccessful_dependency = next(
            (name for name in component.depends_on if name in unsuccessful_names), None
        )
        if unsuccessful_dependency is not None:
            result = skipped_result(component, unsuccessful_dependency)
        else:
            result = execute_component(component, reporter, log_capture)
        if result.outcome is not ComponentOutcome.SUCCEEDED:
            unsuccessful_names.add(component.name)
        reporter.component_finished(result)
        results.append(result)

    reporter.run_finished(results, time.monotonic() - started_at)
    if unsuccessful_names:
        return EXIT_FAILURE
    changed_anything = any(
        operation.changed
        for result in results
        for operation in result.operation_results
    )
    if options.fail_on_change and changed_anything:
        return EXIT_CHANGES_DETECTED
    return EXIT_SUCCESS
