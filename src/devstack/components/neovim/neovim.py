import shlex
from pathlib import Path

from devstack.commands import run_command
from devstack.github import clone_github_repository
from devstack.mise import MISE_IS_INSTALLED, install_mise_tools, mise_exec
from devstack.pyinfra_adapters import component_deploy
from devstack.requirement import Requirement
from devstack.shells import add_bash_snippet, add_nushell_snippet
from devstack.updates.step import StepOutcome, UpdateContext, UpdateStep
from devstack.updates.version_bump import commit_and_offer_push

FILES = Path(__file__).resolve().parent / "files"
RESTORE_PLUGINS_COMMAND = (
    "lua vim.pack.update(nil, { target = 'lockfile', force = true })"
)
POST_INSTALL_COMMAND = "lua require('post-install').run()"
UPGRADE_PLUGINS_COMMAND = "lua vim.pack.update(nil, { force = true })"
CONFIG_DIRECTORY = Path.home() / ".config/nvim"


def headless_neovim_command(*vim_commands: str) -> str:
    arguments = mise_exec("nvim", "--headless")
    for vim_command in vim_commands:
        arguments += ["-c", vim_command]
    return shlex.join(arguments)


@component_deploy("neovim")
def apply_neovim() -> None:
    install_mise_tools("neovim", FILES / "mise.toml")

    configuration = clone_github_repository("ll-nick/neovim-config", CONFIG_DIRECTORY)
    run_command(
        "Install neovim plugins",
        headless_neovim_command(RESTORE_PLUGINS_COMMAND, "qa"),
        when_any_changed=[configuration],
    )
    run_command(
        "Run neovim post-install hooks",
        headless_neovim_command(POST_INSTALL_COMMAND),
        when_any_changed=[configuration],
    )

    add_bash_snippet(FILES / "nvim.bash")
    add_nushell_snippet(FILES / "nvim.nu")


def update_neovim(context: UpdateContext) -> StepOutcome:
    context.section("Updating Neovim Plugins ✨")
    # Unlike a restore, a bump moves the lockfile, which is then committed
    plugin_command = (
        UPGRADE_PLUGINS_COMMAND if context.bump_versions else RESTORE_PLUGINS_COMMAND
    )
    context.run([*mise_exec("nvim", "--headless"), "-c", plugin_command, "-c", "qa"])
    context.run([*mise_exec("nvim", "--headless"), "-c", POST_INSTALL_COMMAND])
    if context.bump_versions:
        commit_and_offer_push(context, CONFIG_DIRECTORY, "nvim-pack-lock.json")
    return StepOutcome.UPDATED


NEOVIM_UPDATE = UpdateStep(
    "neovim",
    update_neovim,
    requires=(
        MISE_IS_INSTALLED,
        Requirement("a neovim config", CONFIG_DIRECTORY.exists),
    ),
)
