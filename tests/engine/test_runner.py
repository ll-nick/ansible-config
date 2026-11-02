from collections.abc import Callable

from stk.engine.component import Component
from stk.engine.runner import run_in_dependency_order
from stk.reporting.reporter import ComponentOutcome, ComponentResult


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
    components = [
        Component("base", noop),
        Component("broken", noop, depends_on=("base",)),
        Component("dependent", noop, depends_on=("broken",)),
        Component("independent", noop, depends_on=("base",)),
    ]

    results = run_in_dependency_order(
        components, make_execute(failing=frozenset({"broken"})), skip
    )

    assert results["broken"].outcome is ComponentOutcome.FAILED
    assert results["dependent"].outcome is ComponentOutcome.SKIPPED
    assert results["dependent"].skipped_because == "broken"
    assert results["independent"].outcome is ComponentOutcome.SUCCEEDED


def test_skips_propagate_through_chains() -> None:
    components = [
        Component("broken", noop),
        Component("middle", noop, depends_on=("broken",)),
        Component("last", noop, depends_on=("middle",)),
    ]

    results = run_in_dependency_order(
        components, make_execute(failing=frozenset({"broken"})), skip
    )

    assert results["middle"].outcome is ComponentOutcome.SKIPPED
    assert results["last"].outcome is ComponentOutcome.SKIPPED


def test_dependencies_outside_the_selection_do_not_block() -> None:
    components = [Component("tool", noop, depends_on=("not-selected",))]

    results = run_in_dependency_order(components, make_execute(), skip)

    assert results["tool"].outcome is ComponentOutcome.SUCCEEDED
