import shlex
import subprocess
from collections.abc import Sequence
from pathlib import Path

from pyinfra.operations import server


def write_generated_file(destination: Path, command: Sequence[str]) -> None:
    if _generated_output_matches_file(destination, command):
        return
    quoted_command = shlex.join(command)
    quoted_destination = shlex.quote(str(destination))
    server.shell(
        name=f"Generate {destination.name}",
        commands=[
            'temporary_file="$(mktemp)"'
            + " && trap 'rm -f \"$temporary_file\"' EXIT"
            + f' && cd "$HOME" && {quoted_command} > "$temporary_file"'
            + f' && install -D -m 644 "$temporary_file" {quoted_destination}'
        ],
    )


def _generated_output_matches_file(destination: Path, command: Sequence[str]) -> bool:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            cwd=Path.home(),
        )
        return destination.read_text() == completed.stdout
    except OSError, subprocess.CalledProcessError:
        return False
