import os
import shlex
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import final

from rich.console import Console
from rich.rule import Rule

from devstack.updates.step import CommandFailedError


@final
class TerminalUpdateContext:
    def __init__(
        self, console: Console, *, assume_yes: bool, bump_versions: bool
    ) -> None:
        self._console = console
        self._assume_yes = assume_yes
        self._bump_versions = bump_versions

    @property
    def assume_yes(self) -> bool:
        return self._assume_yes

    @property
    def bump_versions(self) -> bool:
        return self._bump_versions

    def section(self, title: str, /) -> None:
        self._console.print()
        self._console.print(Rule(f"[green]{title}", style="blue"))

    def confirm(self, question: str, /) -> bool:
        if self._assume_yes:
            return True
        answer = self._console.input(f"{question} \\[y/N]: ").strip().lower()
        if answer in ("y", "yes"):
            return True
        self._console.print("Skipping...")
        return False

    def run(
        self,
        command: Sequence[str],
        *,
        working_directory: Path | None = None,
        environment: Mapping[str, str] | None = None,
    ) -> None:
        self._console.print(f"[dim]$ {shlex.join(command)}", highlight=False)
        completed = subprocess.run(
            command,
            cwd=working_directory,
            env={**os.environ, **(environment or {})},
            check=False,
        )
        if completed.returncode != 0:
            raise CommandFailedError(command, completed.returncode)
