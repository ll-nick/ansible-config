from stk.testing import RecordingContext
from stk_config.components.nixos.nixos import FLAKE_DIRECTORY, update_nixos


def test_bumping_updates_the_flake_before_switching() -> None:
    context = RecordingContext()
    context.bump_versions = True
    context.nothing_staged = True

    update_nixos(context)

    assert context.commands[0] == ["nix", "flake", "update"]
    assert ["sudo", "nixos-rebuild", "switch", "--flake", str(FLAKE_DIRECTORY)] in (
        context.commands
    )


def test_without_bumping_the_flake_stays_as_it_is() -> None:
    context = RecordingContext()

    update_nixos(context)

    assert context.commands[0][:3] == ["sudo", "nixos-rebuild", "switch"]
