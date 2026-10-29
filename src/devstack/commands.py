from collections.abc import Sequence

from pyinfra.api.operation import OperationMeta
from pyinfra.operations import server
from pyinfra.operations.util import any_changed


def run_command(
    name: str,
    command: str,
    *,
    when_any_changed: Sequence[OperationMeta] = (),
) -> None:
    if when_any_changed:
        server.shell(name=name, commands=[command], _if=any_changed(*when_any_changed))
    else:
        server.shell(name=name, commands=[command])
