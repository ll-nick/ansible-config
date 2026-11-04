from collections.abc import Callable
from dataclasses import dataclass

from stk.engine.requirement import Requirement, first_unmet_requirement
from stk.engine.update_step import UpdateStep

DEFAULT_GROUP = "default"


def no_user_work() -> None:
    pass


@dataclass(frozen=True)
class PrivilegedTask:
    """Work a component does as root, before everything that runs without it."""

    description: str
    # Runs without root, to decide whether to ask for the password at all
    is_pending: Callable[[], bool]
    # All operations it queues run with sudo
    apply: Callable[[], None]


@dataclass(frozen=True)
class Component:
    name: str
    apply: Callable[[], object] = no_user_work
    depends_on: tuple[Component, ...] = ()
    requires: tuple[Requirement, ...] = ()
    system_packages: tuple[str, ...] = ()
    privileged_tasks: tuple[PrivilegedTask, ...] = ()
    update: UpdateStep | None = None
    groups: tuple[str, ...] = (DEFAULT_GROUP,)

    @property
    def dependency_names(self) -> tuple[str, ...]:
        return tuple(dependency.name for dependency in self.depends_on)

    def unmet_requirement(self) -> Requirement | None:
        return first_unmet_requirement(self.requires)
