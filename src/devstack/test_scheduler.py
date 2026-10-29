import time
from collections.abc import Callable

import gevent

from devstack.component import Component
from devstack.reporting import ComponentOutcome, ComponentResult
from devstack.scheduler import schedule_components

PAUSE_SECONDS = 0.05


def noop() -> None:
    pass


def result(name: str, outcome: ComponentOutcome) -> ComponentResult:
    return ComponentResult(name, outcome, (), 0.0)


def make_execute(
    failing: frozenset[str] | None = None,
    log: list[str] | None = None,
) -> Callable[[Component], ComponentResult]:
    failing_names = failing or frozenset()

    def execute(component: Component) -> ComponentResult:
        if log is not None:
            log.append(f"start {component.name}")
        gevent.sleep(PAUSE_SECONDS)
        if log is not None:
            log.append(f"end {component.name}")
        outcome = (
            ComponentOutcome.FAILED
            if component.name in failing_names
            else ComponentOutcome.SUCCEEDED
        )
        return result(component.name, outcome)

    return execute


def skip(component: Component, blocker: str) -> ComponentResult:
    return ComponentResult(
        component.name, ComponentOutcome.SKIPPED, (), 0.0, skipped_because=blocker
    )


def test_independent_components_run_concurrently() -> None:
    components = [Component(name, noop) for name in "abcd"]

    started_at = time.monotonic()
    results = schedule_components(components, make_execute(), skip, jobs=4)

    assert time.monotonic() - started_at < PAUSE_SECONDS * 2.5
    assert len(results) == 4


def test_jobs_limit_the_concurrency() -> None:
    components = [Component(name, noop) for name in "abcd"]

    started_at = time.monotonic()
    schedule_components(components, make_execute(), skip, jobs=1)

    assert time.monotonic() - started_at >= PAUSE_SECONDS * 4


def test_dependents_start_after_their_dependencies_finish() -> None:
    log: list[str] = []
    components = [
        Component("base", noop),
        Component("tool", noop, depends_on=("base",)),
    ]

    schedule_components(components, make_execute(log=log), skip, jobs=4)

    assert log == ["start base", "end base", "start tool", "end tool"]


def test_failure_skips_dependents_but_not_independent_components() -> None:
    components = [
        Component("base", noop),
        Component("broken", noop, depends_on=("base",)),
        Component("dependent", noop, depends_on=("broken",)),
        Component("independent", noop, depends_on=("base",)),
    ]

    results = schedule_components(
        components, make_execute(failing=frozenset({"broken"})), skip, jobs=4
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

    results = schedule_components(
        components, make_execute(failing=frozenset({"broken"})), skip, jobs=2
    )

    assert results["middle"].outcome is ComponentOutcome.SKIPPED
    assert results["last"].outcome is ComponentOutcome.SKIPPED
