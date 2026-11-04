from stk.enablement import SUDO_ENTRY
from stk.engine.requirement import Requirement
from stk.engine.update_step import StepOutcome, UpdateContext, UpdateStep
from stk.setup import Setup


def update_stk(context: UpdateContext, setup: Setup) -> StepOutcome:
    context.section("Updating stk 🛠️")
    context.run(["git", "pull", "--ff-only"], working_directory=setup.checkout)
    # A new process, because the pull may have changed the code that is running
    skip_sudo = () if context.may_use_sudo else ("--skip", SUDO_ENTRY)
    context.run([str(setup.command), "apply", "--yes", *skip_sudo])
    return StepOutcome.UPDATED


def stk_update_step(setup: Setup) -> UpdateStep:
    command_exists = Requirement(
        f"the stk command {setup.command}", setup.command.exists
    )
    checkout_exists = Requirement(
        f"a checkout at {setup.checkout}", lambda: (setup.checkout / ".git").exists()
    )
    return UpdateStep(
        "stk",
        lambda context: update_stk(context, setup),
        requires=(command_exists, checkout_exists),
    )
