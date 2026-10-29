from collections.abc import Callable, Sequence

from devstack.component import Component
from devstack.concurrency import TaskSet
from devstack.reporting import ComponentOutcome, ComponentResult


def schedule_components(
    components: Sequence[Component],
    execute: Callable[[Component], ComponentResult],
    skip: Callable[[Component, str], ComponentResult],
    jobs: int,
) -> dict[str, ComponentResult]:
    selected_names = {component.name for component in components}
    results: dict[str, ComponentResult] = {}
    pending = list(components)
    running: TaskSet[str, ComponentResult] = TaskSet()

    def selected_dependencies(component: Component) -> list[str]:
        return [name for name in component.depends_on if name in selected_names]

    def unsuccessful_dependency(component: Component) -> str | None:
        for name in selected_dependencies(component):
            result = results.get(name)
            if result is not None and result.outcome is not ComponentOutcome.SUCCEEDED:
                return name
        return None

    def settle_skipped() -> None:
        changed = True
        while changed:
            changed = False
            for component in list(pending):
                blocker = unsuccessful_dependency(component)
                if blocker is not None:
                    pending.remove(component)
                    results[component.name] = skip(component, blocker)
                    changed = True

    while pending or len(running):
        settle_skipped()
        for component in list(pending):
            if len(running) >= jobs:
                break
            if all(name in results for name in selected_dependencies(component)):
                pending.remove(component)
                running.start(component.name, _bind(execute, component))
        if not len(running):
            break
        for name, result in running.wait_for_any():
            results[name] = result

    return results


def _bind(
    execute: Callable[[Component], ComponentResult], component: Component
) -> Callable[[], ComponentResult]:
    return lambda: execute(component)
