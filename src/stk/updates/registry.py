from dataclasses import replace
from pathlib import Path

from stk.engine.component import Component
from stk.engine.update_step import UpdateStep
from stk.updates.steps.dotfiles import dotfiles_update_step
from stk.updates.steps.system import HAS_SYSTEM_PACKAGE_MANAGER, update_system


def core_update_steps(checkout: Path) -> tuple[UpdateStep, ...]:
    # Not owned by a component, and the first to run:
    # a newer configuration and fresh system packages are what the component steps
    # build on
    return (
        UpdateStep(
            "system",
            update_system,
            requires=(HAS_SYSTEM_PACKAGE_MANAGER,),
            uses_sudo=True,
        ),
        dotfiles_update_step(checkout),
    )


def component_update_steps(
    components: tuple[Component, ...],
) -> tuple[UpdateStep, ...]:
    # A component's step only makes sense where the component itself applies
    return tuple(
        replace(
            component.update, requires=(*component.requires, *component.update.requires)
        )
        for component in components
        if component.update is not None
    )


def all_update_steps(
    checkout: Path, components: tuple[Component, ...]
) -> tuple[UpdateStep, ...]:
    return (*core_update_steps(checkout), *component_update_steps(components))
