from collections.abc import Sequence

import pytest
from pyinfra.api.state import BaseStateCallback

from stk import system_packages
from stk.commands import run_command
from stk.component import Component, PrivilegedTask
from stk.pyinfra_adapters import operation_order
from stk.requirement import Requirement
from stk.runner import prepare_state
from stk.system_packages import (
    SYSTEM_PACKAGES_COMPONENT_NAME,
    merged_packages,
    pending_sudo_work,
    with_privileged_work,
)


def noop() -> None:
    pass


def pending_task(description: str) -> PrivilegedTask:
    return PrivilegedTask(description, lambda: True, noop)


def settled_task(description: str) -> PrivilegedTask:
    return PrivilegedTask(description, lambda: False, noop)


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

    assert pending_sudo_work(components) == []
    assert with_privileged_work(components) == components


def test_only_missing_packages_are_sudo_work(monkeypatch: pytest.MonkeyPatch) -> None:
    use_distributions(monkeypatch, "ubuntu", "debian")
    only_git_is_installed(monkeypatch)
    components = [
        Component("git", noop, system_packages=("git", "unzip")),
        Component("locale", noop, privileged_tasks=(pending_task("generate"),)),
        Component("done", noop, privileged_tasks=(settled_task("generate"),)),
    ]

    assert pending_sudo_work(components) == [
        "system-packages: install unzip",
        "locale: generate",
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

    result = with_privileged_work(components)

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
        component.name: component for component in with_privileged_work(components)
    }

    assert by_name["gui"].depends_on == ()


def test_nothing_is_added_when_no_component_needs_packages() -> None:
    components = [Component("fd", noop)]

    assert with_privileged_work(components) == components


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

    assert with_privileged_work(components) == components


def test_inapplicable_components_are_no_sudo_work(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    use_distributions(monkeypatch, "debian")
    unmet = Requirement("a display", lambda: False)
    components = [
        Component(
            "gui",
            noop,
            requires=(unmet,),
            system_packages=("fontconfig",),
            privileged_tasks=(pending_task("generate"),),
        )
    ]

    assert pending_sudo_work(components) == []


def test_a_pending_task_runs_before_its_component_and_after_the_packages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    use_distributions(monkeypatch, "debian")
    components = [
        Component(
            "locale",
            noop,
            system_packages=("locales",),
            privileged_tasks=(pending_task("generate"),),
        ),
        Component("fd", noop),
    ]

    result = with_privileged_work(components)

    by_name = {component.name: component for component in result}
    assert [component.name for component in result] == [
        SYSTEM_PACKAGES_COMPONENT_NAME,
        "locale-privileged",
        "locale",
        "fd",
    ]
    assert by_name["locale-privileged"].depends_on == (SYSTEM_PACKAGES_COMPONENT_NAME,)
    assert "locale-privileged" in by_name["locale"].depends_on
    assert "locale-privileged" not in by_name["fd"].depends_on


def test_settled_tasks_add_nothing() -> None:
    components = [Component("locale", noop, privileged_tasks=(settled_task("x"),))]

    assert with_privileged_work(components) == components


def test_the_operations_of_a_task_run_with_sudo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    use_distributions(monkeypatch, "nixos")

    def generate() -> None:
        run_command("Generate", "true")

    task = PrivilegedTask("generate", lambda: True, generate)
    privileged = with_privileged_work(
        [Component("locale", noop, privileged_tasks=(task,))]
    )[0]

    state = prepare_state(privileged, BaseStateCallback(), None)

    host = next(iter(state.inventory.get_active_hosts()))
    op_hash = operation_order(state)[0]
    arguments = state.get_op_data_for_host(host, op_hash).global_arguments
    assert arguments["_sudo"]  # pyright: ignore[reportTypedDictNotRequiredAccess]
