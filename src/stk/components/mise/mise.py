from stk.commands import run_command
from stk.mise import MISE_INSTALL_SCRIPT_URL, MISE_IS_INSTALLED, mise_executable
from stk.pyinfra_adapters import component_deploy
from stk.updates.step import StepOutcome, UpdateContext, UpdateStep

PREBUILT_BINARIES_ONLY = {"MISE_NODE_COMPILE": "false", "MISE_PYTHON_COMPILE": "false"}


@component_deploy("mise")
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
