from collections.abc import Callable
from dataclasses import dataclass

from stk.requirement import Requirement, first_unmet_requirement
from stk.updates.step import UpdateStep


@dataclass(frozen=True)
class Component:
    name: str
    apply: Callable[[], object]
    depends_on: tuple[str, ...] = ()
    requires: tuple[Requirement, ...] = ()
    system_packages: tuple[str, ...] = ()
    update: UpdateStep | None = None
    optional: bool = False
    # What the component would do as root, checked without root before asking for sudo
    pending_sudo_work: Callable[[], str | None] | None = None

    def unmet_requirement(self) -> Requirement | None:
        return first_unmet_requirement(self.requires)
