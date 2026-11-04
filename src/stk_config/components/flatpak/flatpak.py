from stk.engine.component import Component
from stk.engine.update_step import StepOutcome, UpdateContext, UpdateStep
from stk.machine import has_executable


def update_flatpak(context: UpdateContext) -> StepOutcome:
    context.section("Updating Flatpak Packages 📦")
    context.run(["flatpak", "update", "--assumeyes"])
    return StepOutcome.UPDATED


FLATPAK = Component(
    "flatpak",
    requires=(has_executable("flatpak"),),
    update=UpdateStep("flatpak", update_flatpak),
)
