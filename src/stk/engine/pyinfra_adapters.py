from pyinfra.api.config import Config
from pyinfra.api.deploy import add_deploy, deploy  # pyright: ignore[reportUnknownVariableType]
from pyinfra.api.inventory import Inventory
from pyinfra.api.state import BaseStateCallback, State

from stk.engine.component import Component

# pyinfra's own type hints are incomplete in these places,
# so the untyped calls are confined to this module.


def create_local_state(
    callbacks: BaseStateCallback, sudo_password: str | None
) -> State:
    state = State(
        inventory=Inventory((["@local"], {})),  # pyright: ignore[reportUnknownArgumentType]
        config=Config(SUDO_PASSWORD=sudo_password),
    )
    state.add_callback_handler(callbacks)  # pyright: ignore[reportUnknownMemberType]
    return state


def prepare_component(state: State, component: Component) -> None:
    # The deploy name prefixes the operation names, which tell reporting the component
    apply = deploy(component.name)(component.apply)
    if component.runs_as_root:
        add_deploy(state, apply, _sudo=True)
    else:
        add_deploy(state, apply)


def operation_order(state: State) -> list[str]:
    return [str(op_hash) for op_hash in state.get_op_order()]  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
