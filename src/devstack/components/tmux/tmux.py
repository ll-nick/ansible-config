from pathlib import Path

from devstack.commands import run_command
from devstack.file_copy import copy_file
from devstack.github import clone_github_repository, clone_repository
from devstack.machine import JOY_HOSTNAME, has_systemd, hostname
from devstack.mise import install_mise_tools, mise_executable
from devstack.pyinfra_adapters import component_deploy
from devstack.shells import add_bash_snippet, add_nushell_snippet
from devstack.systemd import USER_UNIT_DIRECTORY, enable_user_unit

FILES = Path(__file__).resolve().parent / "files"
TMUX_PLUGIN_MANAGER_URL = "https://github.com/tmux-plugins/tpm"


@component_deploy("tmux")
def apply_tmux() -> None:
    config_directory = Path.home() / ".config" / "tmux"
    plugin_manager_directory = config_directory / "plugins" / "tpm"
    plugin_installer = plugin_manager_directory / "bin" / "install_plugins"

    install_mise_tools("tmux", FILES / "mise.toml")

    configuration = clone_github_repository("ll-nick/tmux-config", config_directory)
    clone_repository(
        TMUX_PLUGIN_MANAGER_URL, plugin_manager_directory, ignore_errors=False
    )
    run_command(
        "Install tmux plugins",
        f"{mise_executable()} exec -- bash {plugin_installer}",
        when_any_changed=[configuration],
    )

    add_bash_snippet(FILES / "tmux.bash")
    add_nushell_snippet(FILES / "tmux.nu")

    # Joy's sessions must survive logouts, so it gets no autostart service
    if has_systemd() and hostname() != JOY_HOSTNAME:
        copy_file(FILES / "tmux.service", USER_UNIT_DIRECTORY / "tmux.service")
        enable_user_unit("tmux")
