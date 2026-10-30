from devstack.updates.step import UpdateStep
from devstack.updates.steps.dotfiles import (
    CHECKOUT_EXISTS,
    UV_IS_INSTALLED,
    update_dotfiles,
)
from devstack.updates.steps.flatpak import FLATPAK_IS_INSTALLED, update_flatpak
from devstack.updates.steps.mise import MISE_IS_INSTALLED, update_mise
from devstack.updates.steps.neovim import NEOVIM_CONFIG_EXISTS, update_neovim
from devstack.updates.steps.system import HAS_SYSTEM_PACKAGE_MANAGER, update_system
from devstack.updates.steps.tmux import TPM_IS_INSTALLED, update_tmux

UPDATE_STEPS: tuple[UpdateStep, ...] = (
    UpdateStep("system", update_system, requires=(HAS_SYSTEM_PACKAGE_MANAGER,)),
    UpdateStep("mise", update_mise, requires=(MISE_IS_INSTALLED,)),
    UpdateStep(
        "dotfiles", update_dotfiles, requires=(UV_IS_INSTALLED, CHECKOUT_EXISTS)
    ),
    UpdateStep("tmux", update_tmux, requires=(MISE_IS_INSTALLED, TPM_IS_INSTALLED)),
    UpdateStep(
        "neovim", update_neovim, requires=(MISE_IS_INSTALLED, NEOVIM_CONFIG_EXISTS)
    ),
    UpdateStep("flatpak", update_flatpak, requires=(FLATPAK_IS_INSTALLED,)),
)
