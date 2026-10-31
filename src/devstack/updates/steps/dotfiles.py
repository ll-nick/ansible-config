import shutil

from devstack.checkout import PERMANENT_CHECKOUT
from devstack.requirement import Requirement
from devstack.updates.step import StepOutcome, UpdateContext

CHECKOUT_EXISTS = Requirement(
    f"a devstack checkout at {PERMANENT_CHECKOUT}",
    lambda: (PERMANENT_CHECKOUT / ".git").exists(),
)
UV_IS_INSTALLED = Requirement("uv", lambda: shutil.which("uv") is not None)


def update_dotfiles(context: UpdateContext) -> StepOutcome:
    context.section("Updating Dotfiles 🛠️")
    context.run(["git", "pull", "--ff-only"], working_directory=PERMANENT_CHECKOUT)
    # A new process, because the pull may have changed the code that is running
    context.run(
        [
            "uv",
            "run",
            "--quiet",
            "--no-dev",
            "--project",
            str(PERMANENT_CHECKOUT),
            "stk",
            "apply",
            "--yes",
        ]
    )
    return StepOutcome.UPDATED
