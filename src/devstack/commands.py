from collections.abc import Sequence

from pyinfra.api.operation import OperationMeta
from pyinfra.operations import server
from pyinfra.operations.util import any_changed

RETRY_DELAY_SECONDS = 2


def run_command(
    name: str,
    command: str,
    *,
    when_any_changed: Sequence[OperationMeta] = (),
    sudo: bool = False,
    retries: int = 0,
) -> None:
    if when_any_changed:
        server.shell(
            name=name,
            commands=[command],
            _if=any_changed(*when_any_changed),
            _sudo=sudo,
            _retries=retries,
            _retry_delay=RETRY_DELAY_SECONDS,
        )
    else:
        server.shell(
            name=name,
            commands=[command],
            _sudo=sudo,
            _retries=retries,
            _retry_delay=RETRY_DELAY_SECONDS,
        )
