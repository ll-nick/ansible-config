from collections.abc import Callable
from typing import cast

from pyinfra.api.config import Config
from pyinfra.api.deploy import add_deploy, deploy  # pyright: ignore[reportUnknownVariableType]
from pyinfra.api.inventory import Inventory
from pyinfra.api.state import BaseStateCallback, State

# pyinfra's own type hints are incomplete in these places,
# so the untyped calls are confined to this module.


def component_deploy(name: str) -> Callable[[Callable[[], None]], Callable[[], None]]:
    return cast(
        "Callable[[Callable[[], None]], Callable[[], None]]",
        deploy(name),
    )


def create_local_state(callbacks: BaseStateCallback) -> State:
    state = State(
        inventory=Inventory((["@local"], {})),  # pyright: ignore[reportUnknownArgumentType]
        config=Config(),
    )
    state.add_callback_handler(callbacks)  # pyright: ignore[reportUnknownMemberType]
    return state


def prepare_component(state: State, apply: Callable[[], object]) -> None:
    add_deploy(state, apply)


def operation_order(state: State) -> list[str]:
    return [str(op_hash) for op_hash in state.get_op_order()]  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
