from pathlib import Path

from devstack.component import Requirement
from devstack.mise import mise_exec
from devstack.updates.step import StepOutcome, UpdateContext

PLUGIN_UPDATER = Path.home() / ".config/tmux/plugins/tpm/bin/update_plugins"
TPM_IS_INSTALLED = Requirement("the tmux plugin manager", PLUGIN_UPDATER.exists)


def update_tmux(context: UpdateContext) -> StepOutcome:
    context.section("Updating Tmux Plugins 🔧")
    if not context.confirm("Update Tmux plugins?"):
        return StepOutcome.DECLINED
    context.run(mise_exec(str(PLUGIN_UPDATER), "all"))
    return StepOutcome.UPDATED
