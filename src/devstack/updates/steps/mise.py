from devstack.component import Requirement
from devstack.mise import mise_executable
from devstack.updates.step import StepOutcome, UpdateContext

MISE_IS_INSTALLED = Requirement("mise", lambda: mise_executable().exists())
PREBUILT_BINARIES_ONLY = {"MISE_NODE_COMPILE": "false", "MISE_PYTHON_COMPILE": "false"}


def update_mise(context: UpdateContext) -> StepOutcome:
    context.section("Updating Mise Packages 📦")
    if not context.confirm("Update mise packages?"):
        return StepOutcome.DECLINED
    confirmation_flags = ["--yes"] if context.assume_yes else []
    mise = str(mise_executable())
    context.run(
        [mise, "self-update", *confirmation_flags], environment=PREBUILT_BINARIES_ONLY
    )
    context.run(
        [mise, "upgrade", *confirmation_flags], environment=PREBUILT_BINARIES_ONLY
    )
    return StepOutcome.UPDATED
