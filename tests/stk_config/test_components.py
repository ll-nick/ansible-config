from pathlib import Path

from stk.engine.component import Component
from stk.engine.registry import discover_components
from stk_config.components.uv.uv import UV

COMPONENTS_DIRECTORY = Path(__file__).resolve().parents[2] / "src/stk_config/components"


def transitive_dependency_names(component: Component) -> set[str]:
    names: set[str] = set()
    for dependency in component.depends_on:
        names.add(dependency.name)
        names |= transitive_dependency_names(dependency)
    return names


def test_components_installing_pipx_tools_run_after_uv() -> None:
    # mise only installs pipx tools through uv once uv is one of its own tools
    components = {
        component.name: component
        for component in discover_components("stk_config.components")
    }
    for tool_config in COMPONENTS_DIRECTORY.glob("*/files/mise.toml"):
        if "pipx:" not in tool_config.read_text():
            continue
        component = components[tool_config.parent.parent.name]
        assert UV.name in transitive_dependency_names(component), component.name
