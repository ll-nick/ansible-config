from pathlib import Path

from devstack.checkout import PERMANENT_CHECKOUT
from devstack.requirement import Requirement
from devstack.updates.step import StepOutcome, UpdateContext

STK_SHIM = Path.home() / ".local/bin/stk"

CHECKOUT_EXISTS = Requirement(
    f"a devstack checkout at {PERMANENT_CHECKOUT}",
    lambda: (PERMANENT_CHECKOUT / ".git").exists(),
)
STK_SHIM_EXISTS = Requirement(f"the stk shim at {STK_SHIM}", STK_SHIM.exists)


def update_dotfiles(context: UpdateContext) -> StepOutcome:
    context.section("Updating Dotfiles 🛠️")
    context.run(["git", "pull", "--ff-only"], working_directory=PERMANENT_CHECKOUT)
    # A new process, because the pull may have changed the code that is running
    context.run([str(STK_SHIM), "apply", "--yes"])
    return StepOutcome.UPDATED
