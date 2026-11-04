from pathlib import Path

from stk.engine.component import Component
from stk.engine.requirement import Requirement
from stk.engine.update_step import StepOutcome, UpdateContext, UpdateStep
from stk.machine import has_executable
from stk.updates.version_bump import commit_and_offer_push

FLAKE_DIRECTORY = Path.home() / ".config/nix"
GENERATIONS_TO_KEEP = "7d"


def update_nixos(context: UpdateContext) -> StepOutcome:
    context.section("Updating NixOS ❄️")
    if context.bump_versions:
        context.run(["nix", "flake", "update"], working_directory=FLAKE_DIRECTORY)
        commit_and_offer_push(context, FLAKE_DIRECTORY, "flake.lock")

    context.run(["sudo", "nixos-rebuild", "switch", "--flake", str(FLAKE_DIRECTORY)])
    context.run(
        ["sudo", "nix-collect-garbage", "--delete-older-than", GENERATIONS_TO_KEEP]
    )
    context.run(["nix", "store", "gc"])
    return StepOutcome.UPDATED


NIXOS = Component(
    "nixos",
    requires=(
        has_executable("nixos-rebuild"),
        Requirement(f"a flake at {FLAKE_DIRECTORY}", FLAKE_DIRECTORY.exists),
    ),
    update=UpdateStep("nixos", update_nixos, uses_sudo=True),
)
