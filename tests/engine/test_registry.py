import sys
from pathlib import Path

import pytest

from stk.engine.component import Component
from stk.engine.registry import (
    MissingComponentError,
    UnknownComponentError,
    direct_dependencies,
    discover_components,
    select_components,
)


def noop() -> None:
    pass


BASE = Component("base", noop)
TOOL = Component("tool", noop, depends_on=(BASE,))
EXTRA = Component("extra", noop, depends_on=(TOOL,))
UNRELATED = Component("unrelated", noop)
AVAILABLE = (BASE, TOOL, EXTRA, UNRELATED)


def names(components: tuple[Component, ...]) -> list[str]:
    return [component.name for component in components]


def test_no_request_selects_everything_in_dependency_order() -> None:
    selected = names(select_components((), AVAILABLE))

    assert sorted(selected) == sorted(component.name for component in AVAILABLE)
    assert selected.index("base") < selected.index("tool") < selected.index("extra")


def test_dependencies_are_pulled_in_before_their_dependents() -> None:
    assert names(select_components(("extra",), AVAILABLE)) == ["base", "tool", "extra"]


def test_unrelated_components_are_not_selected() -> None:
    assert "unrelated" not in names(select_components(("tool",), AVAILABLE))


def test_unknown_component_is_rejected() -> None:
    with pytest.raises(UnknownComponentError, match="nope"):
        select_components(("nope",), AVAILABLE)


def test_direct_dependencies_leave_out_what_another_dependency_pulls_in() -> None:
    component = Component("combined", noop, depends_on=(BASE, EXTRA, UNRELATED))

    assert direct_dependencies(component, (*AVAILABLE, component)) == (
        "extra",
        "unrelated",
    )


def write_component_module(package: Path, name: str, source: str) -> None:
    (package / name).mkdir(parents=True)
    (package / name / "__init__.py").write_text("")
    (package / name / f"{name}.py").write_text(source)


def test_discovery_finds_each_declared_component_in_dependency_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    package = tmp_path / "discovered_components"
    package.mkdir()
    (package / "__init__.py").write_text("")
    write_component_module(
        package,
        "app",
        "from discovered_components.base.base import BASE\n"
        + "from stk.engine.component import Component\n"
        + 'APP = Component("app", depends_on=(BASE,))\n',
    )
    write_component_module(
        package,
        "base",
        'from stk.engine.component import Component\nBASE = Component("base")\n',
    )
    monkeypatch.setattr(sys, "path", [str(tmp_path), *sys.path])

    assert names(discover_components("discovered_components")) == ["base", "app"]


def test_discovery_rejects_a_module_without_its_component(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    package = tmp_path / "incomplete_components"
    package.mkdir()
    (package / "__init__.py").write_text("")
    write_component_module(package, "tool", "TOOL = None\n")
    monkeypatch.setattr(sys, "path", [str(tmp_path), *sys.path])

    with pytest.raises(MissingComponentError, match="no component named tool"):
        discover_components("incomplete_components")
