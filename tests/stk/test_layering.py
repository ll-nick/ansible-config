import ast
from pathlib import Path

import stk

TOOL_DIRECTORY = Path(stk.__file__).parent
CONFIGURATION_PACKAGE = "stk_config"


def imported_modules(path: Path) -> list[str]:
    modules: list[str] = []
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.append(node.module)
    return modules


def test_the_tool_never_imports_the_configuration() -> None:
    imports_of_the_configuration = [
        f"{path.relative_to(TOOL_DIRECTORY)} imports {module}"
        for path in sorted(TOOL_DIRECTORY.rglob("*.py"))
        for module in imported_modules(path)
        if module.partition(".")[0] == CONFIGURATION_PACKAGE
    ]

    assert imports_of_the_configuration == []
