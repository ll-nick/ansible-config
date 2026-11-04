from pathlib import Path

from stk.enablement import SUDO_ENTRY
from stk.engine.requirement import Requirement
from stk.engine.update_step import StepOutcome, UpdateContext, UpdateStep

STK_SHIM = Path.home() / ".local/bin/stk"
STK_SHIM_EXISTS = Requirement(f"the stk shim at {STK_SHIM}", STK_SHIM.exists)


def update_dotfiles(context: UpdateContext, checkout: Path) -> StepOutcome:
    context.section("Updating Dotfiles 🛠️")
    context.run(["git", "pull", "--ff-only"], working_directory=checkout)
    # A new process, because the pull may have changed the code that is running
    skip_sudo = () if context.may_use_sudo else ("--skip", SUDO_ENTRY)
    context.run([str(STK_SHIM), "apply", "--yes", *skip_sudo])
    return StepOutcome.UPDATED


def dotfiles_update_step(checkout: Path) -> UpdateStep:
    checkout_exists = Requirement(
        f"an stk checkout at {checkout}", lambda: (checkout / ".git").exists()
    )
    return UpdateStep(
        "dotfiles",
        lambda context: update_dotfiles(context, checkout),
        requires=(STK_SHIM_EXISTS, checkout_exists),
    )
