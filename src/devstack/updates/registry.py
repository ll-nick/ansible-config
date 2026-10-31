from dataclasses import replace

from devstack.component import Component
from devstack.components import COMPONENTS
from devstack.updates.step import UpdateStep
from devstack.updates.steps.dotfiles import (
    CHECKOUT_EXISTS,
    UV_IS_INSTALLED,
    update_dotfiles,
)
from devstack.updates.steps.flatpak import FLATPAK_IS_INSTALLED, update_flatpak
from devstack.updates.steps.system import HAS_SYSTEM_PACKAGE_MANAGER, update_system

# Not owned by a component, and the first to run:
# a newer devstack and fresh system packages are what the component steps build on
CORE_UPDATE_STEPS: tuple[UpdateStep, ...] = (
    UpdateStep("system", update_system, requires=(HAS_SYSTEM_PACKAGE_MANAGER,)),
    UpdateStep(
        "dotfiles", update_dotfiles, requires=(UV_IS_INSTALLED, CHECKOUT_EXISTS)
    ),
    UpdateStep("flatpak", update_flatpak, requires=(FLATPAK_IS_INSTALLED,)),
)


def component_update_steps(
    components: tuple[Component, ...] = COMPONENTS,
) -> tuple[UpdateStep, ...]:
    # A component's step only makes sense where the component itself applies
    return tuple(
        replace(
            component.update, requires=(*component.requires, *component.update.requires)
        )
        for component in components
        if component.update is not None
    )


def all_update_steps() -> tuple[UpdateStep, ...]:
    return (*CORE_UPDATE_STEPS, *component_update_steps())
