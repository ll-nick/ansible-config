from pathlib import Path

from stk.engine.component import Component
from stk.helpers.archives import download_and_extract_zip
from stk.machine import HAS_DISPLAY

NERD_FONTS_VERSION = "3.1.1"
FONT_ARCHIVE_URL = (
    "https://github.com/ryanoasis/nerd-fonts/releases/download"
    + f"/v{NERD_FONTS_VERSION}/JetBrainsMono.zip"
)
FONTS_DIRECTORY = Path.home() / ".local/share/fonts"


def apply_nerdfont() -> None:
    if not any(FONTS_DIRECTORY.glob("JetBrainsMono*")):
        download_and_extract_zip(FONT_ARCHIVE_URL, FONTS_DIRECTORY)


NERDFONT = Component(
    "nerdfont",
    apply_nerdfont,
    requires=(HAS_DISPLAY,),
    system_packages=("fontconfig", "fonts-noto", "unzip"),
)
