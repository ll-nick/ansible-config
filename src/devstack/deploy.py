from pathlib import Path

from pyinfra import local

COMPONENTS_DIRECTORY = Path(__file__).resolve().parent / "components"

local.include(str(COMPONENTS_DIRECTORY / "fd.py"))  # pyright: ignore[reportUnknownMemberType]
