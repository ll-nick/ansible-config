from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Requirement:
    description: str
    is_met: Callable[[], bool]


def first_unmet_requirement(
    requirements: tuple[Requirement, ...],
) -> Requirement | None:
    for requirement in requirements:
        if not requirement.is_met():
            return requirement
    return None
