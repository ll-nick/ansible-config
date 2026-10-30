from pathlib import Path

from devstack.archives import download_and_extract_zip
from devstack.pyinfra_adapters import component_deploy

NERD_FONTS_VERSION = "3.1.1"
FONT_ARCHIVE_URL = (
    "https://github.com/ryanoasis/nerd-fonts/releases/download"
    + f"/v{NERD_FONTS_VERSION}/JetBrainsMono.zip"
)
FONTS_DIRECTORY = Path.home() / ".local/share/fonts"


@component_deploy("nerdfont")
def apply_nerdfont() -> None:
    if not any(FONTS_DIRECTORY.glob("JetBrainsMono*")):
        download_and_extract_zip(FONT_ARCHIVE_URL, FONTS_DIRECTORY)
