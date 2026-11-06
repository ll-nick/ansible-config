from collections.abc import Callable
from pathlib import Path

from pyinfra.api.state import BaseStateCallback
from pyinfra.operations import files

from stk.engine.component import Component
from stk.engine.pyinfra_adapters import operation_order
from stk.engine.runner import collect_plan, prepare_state, run_in_dependency_order
from stk.helpers.commands import run_command
from stk.reporting.reporter import ComponentOutcome, ComponentResult, PlannedChange


def noop() -> None:
    pass


def make_execute(
    failing: frozenset[str] | None = None,
) -> Callable[[Component], ComponentResult]:
    failing_names = failing or frozenset()

    def execute(component: Component) -> ComponentResult:
        outcome = (
            ComponentOutcome.FAILED
            if component.name in failing_names
            else ComponentOutcome.SUCCEEDED
        )
        return ComponentResult(component.name, outcome, (), 0.0)

    return execute


def skip(component: Component, blocker: str) -> ComponentResult:
    return ComponentResult(
        component.name, ComponentOutcome.SKIPPED, (), 0.0, skipped_because=blocker
    )


def test_failure_skips_dependents_but_not_independent_components() -> None:
    base = Component("base", noop)
    broken = Component("broken", noop, depends_on=(base,))
    components = [
        base,
        broken,
        Component("dependent", noop, depends_on=(broken,)),
        Component("independent", noop, depends_on=(base,)),
    ]

    results = run_in_dependency_order(
        components, make_execute(failing=frozenset({"broken"})), skip
    )

    assert results["broken"].outcome is ComponentOutcome.FAILED
    assert results["dependent"].outcome is ComponentOutcome.SKIPPED
    assert results["dependent"].skipped_because == "broken"
    assert results["independent"].outcome is ComponentOutcome.SUCCEEDED


def test_skips_propagate_through_chains() -> None:
    broken = Component("broken", noop)
    middle = Component("middle", noop, depends_on=(broken,))
    components = [broken, middle, Component("last", noop, depends_on=(middle,))]

    results = run_in_dependency_order(
        components, make_execute(failing=frozenset({"broken"})), skip
    )

    assert results["middle"].outcome is ComponentOutcome.SKIPPED
    assert results["last"].outcome is ComponentOutcome.SKIPPED


def test_dependencies_outside_the_selection_do_not_block() -> None:
    not_selected = Component("not-selected", noop)
    components = [Component("tool", noop, depends_on=(not_selected,))]

    results = run_in_dependency_order(components, make_execute(), skip)

    assert results["tool"].outcome is ComponentOutcome.SUCCEEDED


def test_operations_are_named_after_their_component() -> None:
    def apply() -> None:
        run_command("Say hello", "true")

    state = prepare_state(Component("greeter", apply), BaseStateCallback(), None)

    op_hash = operation_order(state)[0]
    assert state.op_meta[op_hash].names == {"greeter | Say hello"}


def plan_changes(path: Path) -> list[PlannedChange]:
    def apply() -> None:
        created = files.file(name="Create marker", path=str(path), present=True)
        run_command(
            "Reload",
            "true",
            when_any_changed=[created],
        )

    state = prepare_state(Component("marker", apply), BaseStateCallback(), None)
    return [planned.change for planned in collect_plan(state)]


def test_a_command_depending_on_a_pending_change_is_planned_to_run(
    tmp_path: Path,
) -> None:
    changes = plan_changes(tmp_path / "missing")

    assert changes == [PlannedChange.WILL_CHANGE, PlannedChange.WILL_CHANGE]


def test_a_command_depending_on_nothing_pending_is_planned_not_to_run(
    tmp_path: Path,
) -> None:
    existing = tmp_path / "existing"
    existing.touch()

    changes = plan_changes(existing)

    assert changes == [PlannedChange.UNCHANGED, PlannedChange.UNCHANGED]
