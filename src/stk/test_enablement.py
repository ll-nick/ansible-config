from pathlib import Path

import pytest

from stk.component import Component
from stk.enablement import (
    NothingEnabledError,
    disable,
    enable,
    enabled_component_names,
    enabled_entries,
    sudo_is_enabled,
)
from stk.registry import without_skipped


def noop() -> None:
    pass


@pytest.fixture(autouse=True)
def separate_state_directory(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))


def test_a_machine_without_a_file_has_nothing_enabled() -> None:
    with pytest.raises(NothingEnabledError, match="stk enable"):
        enabled_entries()
    assert not sudo_is_enabled()


def test_the_first_enable_includes_the_default_components() -> None:
    assert enable(()) == ("default",)
    assert disable(("default",), ()) == ()
    assert enabled_entries() == ()


def test_adding_a_name_on_a_new_machine_keeps_the_defaults() -> None:
    assert enable(("sudo",)) == ("default", "sudo")
    assert sudo_is_enabled()


def test_enabling_twice_does_not_duplicate_entries() -> None:
    enable(("flatpak",))

    assert enable(("flatpak",)) == ("default", "flatpak")


def test_components_are_selected_by_name_or_by_group() -> None:
    components = [
        Component("base", noop),
        Component("flatpak", noop, groups=()),
    ]

    assert enabled_component_names(("default",), components) == ("base",)
    assert enabled_component_names(("default", "flatpak"), components) == (
        "base",
        "flatpak",
    )
    assert enabled_component_names(("flatpak",), components) == ("flatpak",)


def test_disabling_a_component_of_a_group_excludes_it() -> None:
    components = [Component("base", noop), Component("other", noop)]
    enable(())

    assert disable(("base",), components) == ("default", "-base")
    assert enabled_component_names(enabled_entries(), components) == ("other",)
    assert disable(("base",), components) == ("default", "-base")


def test_enabling_an_excluded_component_lifts_the_exclusion() -> None:
    components = [Component("base", noop)]
    enable(())
    disable(("base",), components)

    assert enable(("base",)) == ("default", "base")
    assert enabled_component_names(enabled_entries(), components) == ("base",)


def test_disabling_a_listed_component_outside_a_group_needs_no_exclusion() -> None:
    components = [Component("flatpak", noop, groups=())]
    enable(("flatpak",))

    assert disable(("flatpak",), components) == ("default",)


def test_an_exclusion_wins_over_a_listed_name() -> None:
    components = [Component("base", noop)]

    assert enabled_component_names(("base", "-base"), components) == ()


def test_unknown_entries_are_left_out() -> None:
    assert enabled_component_names(("removed",), [Component("a", noop)]) == ()


def test_skipping_removes_transitive_dependents() -> None:
    components = [
        Component("base", noop),
        Component("middle", noop, depends_on=("base",)),
        Component("top", noop, depends_on=("middle",)),
        Component("other", noop),
    ]

    kept, dependents = without_skipped(components, ("base",))

    assert [component.name for component in kept] == ["other"]
    assert dependents == ("middle", "top")
