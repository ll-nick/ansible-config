import shlex
from pathlib import Path

from devstack.commands import run_command
from devstack.github import clone_github_repository
from devstack.mise import install_mise_tools, mise_executable
from devstack.pyinfra_adapters import component_deploy
from devstack.shells import add_bash_snippet, add_nushell_snippet

FILES = Path(__file__).resolve().parent / "files"
RESTORE_PLUGINS_COMMAND = (
    "lua vim.pack.update(nil, { target = 'lockfile', force = true })"
)
POST_INSTALL_COMMAND = "lua require('post-install').run()"


def headless_neovim_command(*vim_commands: str) -> str:
    arguments = [str(mise_executable()), "exec", "--", "nvim", "--headless"]
    for vim_command in vim_commands:
        arguments += ["-c", vim_command]
    return shlex.join(arguments)


@component_deploy("neovim")
def apply_neovim() -> None:
    install_mise_tools("neovim", FILES / "mise.toml")

    configuration = clone_github_repository(
        "ll-nick/neovim-config", Path.home() / ".config/nvim"
    )
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
