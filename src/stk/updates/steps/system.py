from stk.engine.update_step import StepOutcome, UpdateContext


def update_system(context: UpdateContext) -> StepOutcome:
    context.section("Updating System Packages 📦")
    context.run(["sudo", "apt", "update"])
    context.run(["sudo", "apt", "upgrade", "--yes"])
    return StepOutcome.UPDATED
