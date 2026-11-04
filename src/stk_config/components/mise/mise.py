from stk.engine.component import Component
from stk.engine.update_step import StepOutcome, UpdateContext, UpdateStep
from stk.helpers.commands import run_command
from stk.helpers.mise import MISE_INSTALL_SCRIPT_URL, MISE_IS_INSTALLED, mise_executable

PREBUILT_BINARIES_ONLY = {"MISE_NODE_COMPILE": "false", "MISE_PYTHON_COMPILE": "false"}


def apply_mise() -> None:
    if not mise_executable().exists():
        # Downloading first, as a failing curl in a pipe would run an empty script
        run_command(
            "Install mise",
            'installer="$(mktemp)"'
            + " && trap 'rm -f \"$installer\"' EXIT"
            + f' && curl -fsSL {MISE_INSTALL_SCRIPT_URL} -o "$installer"'
            + ' && sh "$installer"',
        )


def update_mise(context: UpdateContext) -> StepOutcome:
    context.section("Updating Mise Packages 📦")
    mise = str(mise_executable())
    context.run([mise, "self-update", "--yes"], environment=PREBUILT_BINARIES_ONLY)
    context.run([mise, "upgrade", "--yes"], environment=PREBUILT_BINARIES_ONLY)
    return StepOutcome.UPDATED


MISE_UPDATE = UpdateStep("mise", update_mise, requires=(MISE_IS_INSTALLED,))


MISE = Component("mise", apply_mise, update=MISE_UPDATE)
