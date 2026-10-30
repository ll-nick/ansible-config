from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Requirement:
    description: str
    is_met: Callable[[], bool]


@dataclass(frozen=True)
class SystemPackages:
    common: tuple[str, ...] = ()
    debian: tuple[str, ...] = ()
    arch: tuple[str, ...] = ()


@dataclass(frozen=True)
class Component:
    name: str
    apply: Callable[[], object]
    depends_on: tuple[str, ...] = ()
    requires: tuple[Requirement, ...] = ()
    system_packages: SystemPackages = SystemPackages()

    def unmet_requirement(self) -> Requirement | None:
        for requirement in self.requires:
            if not requirement.is_met():
                return requirement
        return None
