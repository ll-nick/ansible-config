import shlex
from pathlib import Path

from stk.commands import run_command
from stk.github import clone_github_repository, clone_repository
from stk.machine import JOY_HOSTNAME, has_systemd, hostname
from stk.mise import MISE_IS_INSTALLED, install_mise_tools, mise_exec
from stk.pyinfra_adapters import component_deploy
from stk.requirement import Requirement
from stk.shells import add_bash_snippet, add_nushell_snippet
from stk.systemd import enable_user_unit, install_user_unit_file
from stk.updates.step import StepOutcome, UpdateContext, UpdateStep

FILES = Path(__file__).resolve().parent / "files"
TMUX_PLUGIN_MANAGER_URL = "https://github.com/tmux-plugins/tpm"
PLUGIN_UPDATER = Path.home() / ".config/tmux/plugins/tpm/bin/update_plugins"


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
        shlex.join(mise_exec("bash", str(plugin_installer))),
        when_any_changed=[configuration],
    )

    add_bash_snippet(FILES / "tmux.bash")
    add_nushell_snippet(FILES / "tmux.nu")

    # Joy's sessions must survive logouts, so it gets no autostart service
    if has_systemd() and hostname() != JOY_HOSTNAME:
        install_user_unit_file(FILES / "tmux.service")
        enable_user_unit("tmux")


def update_tmux(context: UpdateContext) -> StepOutcome:
    context.section("Updating Tmux Plugins 🔧")
    context.run(mise_exec(str(PLUGIN_UPDATER), "all"))
    return StepOutcome.UPDATED


TMUX_UPDATE = UpdateStep(
    "tmux",
    update_tmux,
    requires=(
        MISE_IS_INSTALLED,
        Requirement("the tmux plugin manager", PLUGIN_UPDATER.exists),
    ),
)
