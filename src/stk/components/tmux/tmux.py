import shlex
from pathlib import Path

from stk.components.bash.bash import BASH
from stk.components.mise.mise import MISE
from stk.components.nushell.nushell import NUSHELL
from stk.engine.component import Component
from stk.engine.requirement import Requirement
from stk.engine.update_step import StepOutcome, UpdateContext, UpdateStep
from stk.helpers.commands import run_command
from stk.helpers.github import clone_github_repository, clone_repository
from stk.helpers.mise import MISE_IS_INSTALLED, install_mise_tools, mise_exec
from stk.helpers.shells import add_bash_snippet, add_nushell_snippet
from stk.helpers.systemd import enable_user_unit, install_user_unit_file
from stk.machine import JOY_HOSTNAME, has_systemd, hostname

FILES = Path(__file__).resolve().parent / "files"
TMUX_PLUGIN_MANAGER_URL = "https://github.com/tmux-plugins/tpm"
PLUGIN_UPDATER = Path.home() / ".config/tmux/plugins/tpm/bin/update_plugins"


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


TMUX = Component(
    "tmux",
    apply_tmux,
    depends_on=(MISE, BASH, NUSHELL),
    system_packages=("xclip",),
    update=TMUX_UPDATE,
)
