from collections.abc import Sequence
from graphlib import TopologicalSorter

from stk.component import Component


class UnknownComponentError(ValueError):
    def __init__(
        self, unknown_names: Sequence[str], known_names: Sequence[str]
    ) -> None:
        super().__init__(
            f"Unknown components: {', '.join(unknown_names)}"
            + f" (known: {', '.join(known_names)})"
        )


def without_skipped(
    components: Sequence[Component], skipped_names: Sequence[str]
) -> tuple[tuple[Component, ...], tuple[str, ...]]:
    """Leaves out the skipped components and everything depending on them."""
    removed_names = set(skipped_names)
    kept: list[Component] = []
    dependents: list[str] = []
    # Dependencies come first in a selection
    for component in components:
        if component.name in removed_names:
            continue
        if removed_names.intersection(component.depends_on):
            removed_names.add(component.name)
            dependents.append(component.name)
            continue
        kept.append(component)
    return tuple(kept), tuple(dependents)


def select_components(
    requested_names: Sequence[str],
    available: Sequence[Component],
) -> tuple[Component, ...]:
    components_by_name = {component.name: component for component in available}
    known_names = list(components_by_name)

    unknown_names = [name for name in requested_names if name not in components_by_name]
    if unknown_names:
        raise UnknownComponentError(unknown_names, known_names)

    needed_names: set[str] = set()
    names_to_visit = list(requested_names or known_names)
    while names_to_visit:
        name = names_to_visit.pop()
        if name in needed_names:
            continue
        needed_names.add(name)
        dependency_names = components_by_name[name].depends_on
        unknown_dependencies = [
            dependency
            for dependency in dependency_names
            if dependency not in components_by_name
        ]
        if unknown_dependencies:
            raise UnknownComponentError(unknown_dependencies, known_names)
        names_to_visit.extend(dependency_names)

    sorter: TopologicalSorter[str] = TopologicalSorter()
    for component in available:
        if component.name in needed_names:
            sorter.add(component.name, *component.depends_on)
    return tuple(components_by_name[name] for name in sorter.static_order())
