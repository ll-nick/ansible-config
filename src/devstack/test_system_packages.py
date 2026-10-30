import pytest

from devstack import system_packages
from devstack.component import Component, Requirement, SystemPackages
from devstack.system_packages import (
    SYSTEM_PACKAGES_COMPONENT_NAME,
    UnsupportedDistributionError,
    packages_for_this_machine,
    with_system_packages,
)


def noop() -> None:
    pass


def use_distributions(monkeypatch: pytest.MonkeyPatch, *identifiers: str) -> None:
    monkeypatch.setattr(
        system_packages, "distribution_ids", lambda: frozenset(identifiers)
    )


def test_packages_are_merged_per_package_manager(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wanted = [
        SystemPackages(common=("git",), debian=("fonts-noto",), arch=("noto-fonts",)),
        SystemPackages(common=("git", "unzip")),
    ]

    use_distributions(monkeypatch, "ubuntu", "debian")
    assert packages_for_this_machine(wanted) == ("apt", ["git", "fonts-noto", "unzip"])

    use_distributions(monkeypatch, "arch")
    assert packages_for_this_machine(wanted) == (
        "pacman",
        ["git", "noto-fonts", "unzip"],
    )


def test_other_distributions_are_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    use_distributions(monkeypatch, "nixos")

    with pytest.raises(UnsupportedDistributionError, match="nixos"):
        packages_for_this_machine([SystemPackages(common=("git",))])


def test_consumers_depend_on_the_installer() -> None:
    components = [
        Component(
            "git",
            noop,
            depends_on=("mise",),
            system_packages=SystemPackages(common=("git",)),
        ),
        Component("fd", noop),
    ]

    result = with_system_packages(components)

    assert result[0].name == SYSTEM_PACKAGES_COMPONENT_NAME
    by_name = {component.name: component for component in result}
    assert by_name["git"].depends_on == ("mise", SYSTEM_PACKAGES_COMPONENT_NAME)
    assert by_name["fd"].depends_on == ()


def test_nothing_is_added_when_no_component_needs_packages() -> None:
    components = [Component("fd", noop)]

    assert with_system_packages(components) == components


def test_inapplicable_components_do_not_pull_in_packages() -> None:
    unmet = Requirement("a display", lambda: False)
    components = [
        Component(
            "gui",
            noop,
            requires=(unmet,),
            system_packages=SystemPackages(common=("fontconfig",)),
        )
    ]

    assert with_system_packages(components) == components
