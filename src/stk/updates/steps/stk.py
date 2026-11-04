import os
import shutil
import sys
from pathlib import Path

from stk.enablement import SUDO_ENTRY
from stk.engine.requirement import Requirement
from stk.engine.update_step import StepOutcome, UpdateContext, UpdateStep
from stk.setup import Setup


def uv_executable() -> str | None:
    # `uv run` names itself in UV, which also finds a uv that is not on PATH
    return os.environ.get("UV") or shutil.which("uv")


HAS_UV = Requirement("uv", lambda: uv_executable() is not None)


def stk_command(checkout: Path) -> list[str]:
    """Runs the command stk was started as from the checkout, synced with its lock."""
    uv = uv_executable()
    if uv is None:
        raise LookupError("uv is needed to run stk from its checkout")
    script_name = Path(sys.argv[0]).name
    return [uv, "run", "--quiet", "--no-dev", "--project", str(checkout), script_name]


def update_stk(context: UpdateContext, setup: Setup) -> StepOutcome:
    context.section("Updating stk 🛠️")
    context.run(["git", "pull", "--ff-only"], working_directory=setup.checkout)
    # A new process, because the pull may have changed the code that is running
    skip_sudo = () if context.may_use_sudo else ("--skip", SUDO_ENTRY)
    context.run([*stk_command(setup.checkout), "apply", "--yes", *skip_sudo])
    return StepOutcome.UPDATED


def stk_update_step(setup: Setup) -> UpdateStep:
    checkout_exists = Requirement(
        f"a checkout at {setup.checkout}", lambda: (setup.checkout / ".git").exists()
    )
    return UpdateStep(
        "stk",
        lambda context: update_stk(context, setup),
        requires=(HAS_UV, checkout_exists),
    )
