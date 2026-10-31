import shutil

from devstack.requirement import Requirement
from devstack.updates.step import StepOutcome, UpdateContext

FLATPAK_IS_INSTALLED = Requirement(
    "flatpak", lambda: shutil.which("flatpak") is not None
)


def update_flatpak(context: UpdateContext) -> StepOutcome:
    context.section("Updating Flatpak Packages 📦")
    context.run(["flatpak", "update", "--assumeyes"])
    return StepOutcome.UPDATED
