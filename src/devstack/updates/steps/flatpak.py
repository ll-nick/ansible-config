import shutil

from devstack.component import Requirement
from devstack.updates.step import StepOutcome, UpdateContext

FLATPAK_IS_INSTALLED = Requirement(
    "flatpak", lambda: shutil.which("flatpak") is not None
)


def update_flatpak(context: UpdateContext) -> StepOutcome:
    context.section("Updating Flatpak Packages 📦")
    if not context.confirm("Update all Flatpak packages?"):
        return StepOutcome.DECLINED
    context.run(["flatpak", "update", *(["--assumeyes"] if context.assume_yes else [])])
    return StepOutcome.UPDATED
