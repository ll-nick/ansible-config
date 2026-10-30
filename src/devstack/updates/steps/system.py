import shutil
from pathlib import Path

from devstack.component import Requirement
from devstack.updates.step import StepOutcome, UpdateContext
from devstack.updates.version_bump import commit_and_offer_push

NIX_FLAKE_DIRECTORY = Path.home() / ".config/nix"
GENERATIONS_TO_KEEP = "7d"


def _has_package_manager() -> bool:
    return shutil.which("apt") is not None or shutil.which("nixos-rebuild") is not None


HAS_SYSTEM_PACKAGE_MANAGER = Requirement("apt or nixos-rebuild", _has_package_manager)


def update_system(context: UpdateContext) -> StepOutcome:
    context.section("Updating System Packages 📦")
    if shutil.which("apt") is not None:
        return _update_with_apt(context)
    return _update_nixos(context)


def _update_with_apt(context: UpdateContext) -> StepOutcome:
    if not context.confirm("Proceed with update via apt?"):
        return StepOutcome.DECLINED
    context.run(["sudo", "apt", "update"])
    context.run(["sudo", "apt", "upgrade", *(["--yes"] if context.assume_yes else [])])
    return StepOutcome.UPDATED


def _update_nixos(context: UpdateContext) -> StepOutcome:
    if not NIX_FLAKE_DIRECTORY.exists():
        context.section(f"Nix flake directory not found at {NIX_FLAKE_DIRECTORY}")
        return StepOutcome.DECLINED

    if context.bump_versions:
        context.run(["nix", "flake", "update"], working_directory=NIX_FLAKE_DIRECTORY)
        commit_and_offer_push(context, NIX_FLAKE_DIRECTORY, "flake.lock")

    outcome = StepOutcome.DECLINED
    if context.confirm("Rebuild system?"):
        context.run(
            ["sudo", "nixos-rebuild", "switch", "--flake", str(NIX_FLAKE_DIRECTORY)]
        )
        outcome = StepOutcome.UPDATED

    if context.confirm("Garbage collect old NixOS generations and store paths?"):
        context.run(
            [
                "sudo",
                "nix-collect-garbage",
                "--delete-older-than",
                GENERATIONS_TO_KEEP,
            ]
        )
        context.run(["nix", "store", "gc"])
    return outcome
