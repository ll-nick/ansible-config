from pathlib import Path

from pyinfra import local

COMPONENTS_DIRECTORY = Path(__file__).resolve().parent / "components"

local.include(str(COMPONENTS_DIRECTORY / "fd" / "fd.py"))  # pyright: ignore[reportUnknownMemberType]

local.include(str(COMPONENTS_DIRECTORY / "bat" / "bat.py"))  # pyright: ignore[reportUnknownMemberType]
