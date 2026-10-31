from pathlib import Path

from devstack.component import Requirement
from devstack.components.neovim.neovim import (
    POST_INSTALL_COMMAND,
    RESTORE_PLUGINS_COMMAND,
)
from devstack.mise import mise_exec
from devstack.updates.step import StepOutcome, UpdateContext
from devstack.updates.version_bump import commit_and_offer_push

NEOVIM_CONFIG_DIRECTORY = Path.home() / ".config/nvim"
UPGRADE_PLUGINS_COMMAND = "lua vim.pack.update(nil, { force = true })"
NEOVIM_CONFIG_EXISTS = Requirement(
    "a neovim config", lambda: NEOVIM_CONFIG_DIRECTORY.exists()
)


def _run_headless(context: UpdateContext, *vim_commands: str) -> None:
    arguments = mise_exec("nvim", "--headless")
    for vim_command in vim_commands:
        arguments += ["-c", vim_command]
    context.run(arguments)


def update_neovim(context: UpdateContext) -> StepOutcome:
    context.section("Updating Neovim Plugins ✨")
    if context.bump_versions:
        _run_headless(context, UPGRADE_PLUGINS_COMMAND, "qa")
        _run_headless(context, POST_INSTALL_COMMAND)
        commit_and_offer_push(context, NEOVIM_CONFIG_DIRECTORY, "nvim-pack-lock.json")
        return StepOutcome.UPDATED

    if not context.confirm("Restore Neovim plugins from lockfile?"):
        return StepOutcome.DECLINED
    _run_headless(context, RESTORE_PLUGINS_COMMAND, "qa")
    _run_headless(context, POST_INSTALL_COMMAND)
    return StepOutcome.UPDATED
