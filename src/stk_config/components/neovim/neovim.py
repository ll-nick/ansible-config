import shlex
from pathlib import Path

from stk.engine.component import Component
from stk.engine.requirement import Requirement
from stk.engine.update_step import StepOutcome, UpdateContext, UpdateStep
from stk.helpers.commands import run_command
from stk.helpers.github import clone_github_repository
from stk.helpers.mise import MISE_IS_INSTALLED, install_mise_tools, mise_exec
from stk.helpers.shells import add_bash_snippet, add_nushell_snippet
from stk.updates.version_bump import commit_and_offer_push
from stk_config.components.bash.bash import BASH
from stk_config.components.fd.fd import FD
from stk_config.components.mise.mise import MISE
from stk_config.components.nodejs.nodejs import NODEJS
from stk_config.components.nushell.nushell import NUSHELL
from stk_config.components.ripgrep.ripgrep import RIPGREP

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


NEOVIM = Component(
    "neovim",
    apply_neovim,
    depends_on=(MISE, BASH, NUSHELL, FD, RIPGREP, NODEJS),
    system_packages=("gcc", "make", "unzip"),
    update=NEOVIM_UPDATE,
)
