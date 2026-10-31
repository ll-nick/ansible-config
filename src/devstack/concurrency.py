from collections.abc import Callable, Sequence
from typing import cast

import gevent
from gevent import Greenlet
from gevent.pool import Pool

# pyinfra runs on gevent, so concurrent work has to be gevent greenlets on the
# main thread; OS threads cannot spawn subprocesses through gevent.

COMPONENT_NAME_KEY = "devstack_component_name"


def _spawn[Result](function: Callable[[], Result]) -> Greenlet[[], Result]:
    return cast("Greenlet[[], Result]", gevent.spawn(function))


class TaskSet[Key, Result]:
    _greenlets: dict[Greenlet[[], Result], Key]

    def __init__(self) -> None:
        self._greenlets = {}

    def __len__(self) -> int:
        return len(self._greenlets)

    def start(self, key: Key, function: Callable[[], Result]) -> None:
        self._greenlets[_spawn(function)] = key

    def wait_for_any(self) -> list[tuple[Key, Result]]:
        finished = gevent.wait(list(self._greenlets), count=1)
        return [
            (self._greenlets.pop(greenlet), greenlet.get()) for greenlet in finished
        ]


def run_all[Result](
    functions: Sequence[Callable[[], Result]], limit: int | None = None
) -> list[Result]:
    pool = Pool(limit)
    greenlets = [pool.spawn(function) for function in functions]
    gevent.joinall(greenlets, raise_error=True)
    return [greenlet.get() for greenlet in greenlets]


def set_current_component_name(component_name: str) -> None:
    spawn_tree_locals = cast(
        "dict[str, str]",
        gevent.getcurrent().spawn_tree_locals,  # pyright: ignore[reportAttributeAccessIssue]
    )
    spawn_tree_locals[COMPONENT_NAME_KEY] = component_name


def current_component_name() -> str | None:
    spawn_tree_locals = getattr(gevent.getcurrent(), "spawn_tree_locals", None)
    if not isinstance(spawn_tree_locals, dict):
        return None
    return cast("dict[str, str]", spawn_tree_locals).get(COMPONENT_NAME_KEY)
