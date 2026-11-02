from pathlib import Path

from stk.enablement import SUDO_ENTRY
from stk.paths import PERMANENT_CHECKOUT
from stk.requirement import Requirement
from stk.update_step import StepOutcome, UpdateContext

STK_SHIM = Path.home() / ".local/bin/stk"

CHECKOUT_EXISTS = Requirement(
    f"an stk checkout at {PERMANENT_CHECKOUT}",
    lambda: (PERMANENT_CHECKOUT / ".git").exists(),
)
STK_SHIM_EXISTS = Requirement(f"the stk shim at {STK_SHIM}", STK_SHIM.exists)


def update_dotfiles(context: UpdateContext) -> StepOutcome:
    context.section("Updating Dotfiles 🛠️")
    context.run(["git", "pull", "--ff-only"], working_directory=PERMANENT_CHECKOUT)
    # A new process, because the pull may have changed the code that is running
    skip_sudo = () if context.may_use_sudo else ("--skip", SUDO_ENTRY)
    context.run([str(STK_SHIM), "apply", "--yes", *skip_sudo])
    return StepOutcome.UPDATED
