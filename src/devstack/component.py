from collections.abc import Callable
from dataclasses import dataclass

from devstack.requirement import Requirement, first_unmet_requirement
from devstack.updates.step import UpdateStep


@dataclass(frozen=True)
class Component:
    name: str
    apply: Callable[[], object]
    depends_on: tuple[str, ...] = ()
    requires: tuple[Requirement, ...] = ()
    system_packages: tuple[str, ...] = ()
    update: UpdateStep | None = None

    def unmet_requirement(self) -> Requirement | None:
        return first_unmet_requirement(self.requires)
