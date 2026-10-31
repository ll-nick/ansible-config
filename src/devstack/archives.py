import shlex
from pathlib import Path

from devstack.commands import run_command


def download_and_extract_zip(url: str, destination: Path) -> None:
    # unzip, unlike Python's zipfile, keeps symbolic links as links
    run_command(
        f"Download and extract {url.rsplit('/', 1)[-1]}",
        'temporary_file="$(mktemp)"'
        + " && trap 'rm -f \"$temporary_file\"' EXIT"
        + f' && curl --fail --location --silent --show-error "{url}"'
        + ' --output "$temporary_file"'
        + f" && mkdir -p {shlex.quote(str(destination))}"
        + f' && unzip -q -o "$temporary_file" -d {shlex.quote(str(destination))}',
    )
