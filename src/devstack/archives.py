import shlex
import sys
from pathlib import Path

from devstack.commands import run_command


def download_and_extract_zip(url: str, destination: Path) -> None:
    # zipfile avoids depending on an installed unzip
    run_command(
        f"Download and extract {url.rsplit('/', 1)[-1]}",
        'temporary_file="$(mktemp)"'
        + " && trap 'rm -f \"$temporary_file\"' EXIT"
        + f' && curl --fail --location --silent --show-error "{url}"'
        + ' --output "$temporary_file"'
        + f" && mkdir -p {shlex.quote(str(destination))}"
        + f' && {shlex.quote(sys.executable)} -m zipfile -e "$temporary_file"'
        + f" {shlex.quote(str(destination))}",
    )
