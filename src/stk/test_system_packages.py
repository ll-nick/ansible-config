from collections.abc import Sequence

import pytest

from stk import system_packages
from stk.component import Component
from stk.requirement import Requirement
from stk.system_packages import (
    SYSTEM_PACKAGES_COMPONENT_NAME,
    merged_packages,
    missing_system_packages,
    pending_sudo_work,
    with_system_packages,
)


def noop() -> None:
    pass


def use_distributions(monkeypatch: pytest.MonkeyPatch, *identifiers: str) -> None:
    monkeypatch.setattr(
        system_packages, "distribution_ids", lambda: frozenset(identifiers)
    )


def only_git_is_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    def installed(_names: Sequence[str]) -> frozenset[str]:
        return frozenset({"git"})

    monkeypatch.setattr(system_packages, "installed_packages", installed)


def test_packages_are_merged_without_duplicates() -> None:
    merged = merged_packages([("git", "fonts-noto"), ("git", "unzip")])

    assert merged == ["git", "fonts-noto", "unzip"]


def test_other_distributions_have_no_system_packages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    use_distributions(monkeypatch, "nixos")
    components = [Component("git", noop, system_packages=("git",))]

    assert missing_system_packages(components) == []
    assert with_system_packages(components) == components


def test_only_missing_packages_are_sudo_work(monkeypatch: pytest.MonkeyPatch) -> None:
    use_distributions(monkeypatch, "ubuntu", "debian")
    only_git_is_installed(monkeypatch)
    components = [
        Component("git", noop, system_packages=("git", "unzip")),
        Component("locale", noop, pending_sudo_work=lambda: "generate a locale"),
        Component("done", noop, pending_sudo_work=lambda: None),
    ]

    assert pending_sudo_work(components) == [
        "system-packages: install unzip",
        "locale: generate a locale",
    ]


def test_nothing_is_sudo_work_when_everything_is_installed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    use_distributions(monkeypatch, "debian")
    only_git_is_installed(monkeypatch)

    assert pending_sudo_work([Component("git", noop, system_packages=("git",))]) == []


def test_all_applicable_components_depend_on_the_installer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    use_distributions(monkeypatch, "debian")
    components = [
        Component(
            "git",
            noop,
            depends_on=("mise",),
            system_packages=("git",),
        ),
        Component("fd", noop),
    ]

    result = with_system_packages(components)

    assert result[0].name == SYSTEM_PACKAGES_COMPONENT_NAME
    by_name = {component.name: component for component in result}
    assert by_name["git"].depends_on == ("mise", SYSTEM_PACKAGES_COMPONENT_NAME)
    assert by_name["fd"].depends_on == (SYSTEM_PACKAGES_COMPONENT_NAME,)


def test_inapplicable_components_do_not_wait_for_the_installer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    use_distributions(monkeypatch, "debian")
    unmet = Requirement("a display", lambda: False)
    components = [
        Component("git", noop, system_packages=("git",)),
        Component("gui", noop, requires=(unmet,)),
    ]

    by_name = {
        component.name: component for component in with_system_packages(components)
    }

    assert by_name["gui"].depends_on == ()


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
            system_packages=("fontconfig",),
        )
    ]

    assert with_system_packages(components) == components
