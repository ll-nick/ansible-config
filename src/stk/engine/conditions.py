from dataclasses import dataclass

from pyinfra.api.operation import OperationMeta


@dataclass(frozen=True)
class AnyChanged:
    """Run an operation only if one of these operations changed something.

    A class instead of a lambda, so planning can resolve it
    from what the dependencies would change.
    """

    dependencies: tuple[OperationMeta, ...]

    def __call__(self) -> bool:
        return any(dependency.did_change() for dependency in self.dependencies)
