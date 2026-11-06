from collections.abc import Sequence

from pyinfra.api.operation import OperationMeta
from pyinfra.operations import server

from stk.engine.conditions import AnyChanged


def run_command(
    name: str,
    command: str,
    *,
    when_any_changed: Sequence[OperationMeta] = (),
) -> None:
    server.shell(
        name=name,
        commands=[command],
        _if=AnyChanged(tuple(when_any_changed)) if when_any_changed else [],
    )
