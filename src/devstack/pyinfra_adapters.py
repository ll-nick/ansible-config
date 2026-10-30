from collections.abc import Callable
from typing import cast

import gevent
from pyinfra.api.config import Config
from pyinfra.api.deploy import add_deploy, deploy  # pyright: ignore[reportUnknownVariableType]
from pyinfra.api.inventory import Inventory
from pyinfra.api.state import BaseStateCallback, State
from pyinfra.context import ctx_state

from devstack.run_settings import run_settings

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
        config=Config(SUDO_PASSWORD=run_settings().sudo_password),
    )
    state.add_callback_handler(callbacks)  # pyright: ignore[reportUnknownMemberType]
    return state


def prepare_component(state: State, apply: Callable[[], object]) -> None:
    add_deploy(state, apply)


def operation_order(state: State) -> list[str]:
    return [str(op_hash) for op_hash in state.get_op_order()]  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]


class _SpawnTreeContainer:
    """Keeps pyinfra's current state per greenlet spawn tree.

    pyinfra stores the current state in a process-wide global, which breaks as soon
    as two states are prepared or run concurrently. Greenlets spawned by a run
    share their parent's spawn tree locals, so each concurrently running component
    sees its own state, including pyinfra's own per-host greenlets.
    """

    _KEY: str = "pyinfra_state"

    def __init__(self) -> None:
        self._main_greenlet_storage: dict[str, object] = {}

    @property
    def module(self) -> object:
        return self._storage().get(self._KEY)

    @module.setter
    def module(self, value: object) -> None:
        self._storage()[self._KEY] = value

    def _storage(self) -> dict[str, object]:
        spawn_tree_locals = getattr(gevent.getcurrent(), "spawn_tree_locals", None)
        if isinstance(spawn_tree_locals, dict):
            return cast("dict[str, object]", spawn_tree_locals)
        return self._main_greenlet_storage


def isolate_state_context_per_greenlet_tree() -> None:
    ctx_state.context._container = _SpawnTreeContainer()  # pyright: ignore[reportUnknownMemberType]


isolate_state_context_per_greenlet_tree()
