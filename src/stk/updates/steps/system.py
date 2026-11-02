import shutil
from pathlib import Path

from stk.requirement import Requirement
from stk.update_step import StepOutcome, UpdateContext
from stk.updates.version_bump import commit_and_offer_push

NIX_FLAKE_DIRECTORY = Path.home() / ".config/nix"
GENERATIONS_TO_KEEP = "7d"


def _has_package_manager() -> bool:
    return shutil.which("apt") is not None or shutil.which("nixos-rebuild") is not None


HAS_SYSTEM_PACKAGE_MANAGER = Requirement("apt or nixos-rebuild", _has_package_manager)


def update_system(context: UpdateContext) -> StepOutcome:
    context.section("Updating System Packages 📦")
    if shutil.which("apt") is not None:
        context.run(["sudo", "apt", "update"])
        context.run(["sudo", "apt", "upgrade", "--yes"])
        return StepOutcome.UPDATED
    return _update_nixos(context)


def _update_nixos(context: UpdateContext) -> StepOutcome:
    if not NIX_FLAKE_DIRECTORY.exists():
        context.note(f"Nix flake directory not found at {NIX_FLAKE_DIRECTORY}")
        return StepOutcome.SKIPPED

    if context.bump_versions:
        context.run(["nix", "flake", "update"], working_directory=NIX_FLAKE_DIRECTORY)
        commit_and_offer_push(context, NIX_FLAKE_DIRECTORY, "flake.lock")

    context.run(
        ["sudo", "nixos-rebuild", "switch", "--flake", str(NIX_FLAKE_DIRECTORY)]
    )
    context.run(
        ["sudo", "nix-collect-garbage", "--delete-older-than", GENERATIONS_TO_KEEP]
    )
    context.run(["nix", "store", "gc"])
    return StepOutcome.UPDATED
