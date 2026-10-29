from collections.abc import Sequence

from devstack.component import Component
from devstack.components import COMPONENTS


class UnknownComponentError(ValueError):
    def __init__(self, unknown_names: Sequence[str]) -> None:
        known_names = ", ".join(component.name for component in COMPONENTS)
        super().__init__(
            f"Unknown components: {', '.join(unknown_names)} (known: {known_names})"
        )


def select_components(requested_names: Sequence[str]) -> tuple[Component, ...]:
    if not requested_names:
        return COMPONENTS

    components_by_name = {component.name: component for component in COMPONENTS}
    unknown_names = [name for name in requested_names if name not in components_by_name]
    if unknown_names:
        raise UnknownComponentError(unknown_names)

    return tuple(components_by_name[name] for name in requested_names)
