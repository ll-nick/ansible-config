from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Component:
    name: str
    apply: Callable[[], object]
