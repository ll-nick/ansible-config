import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import final

import pytest

from stk.engine.requirement import Requirement
from stk.helpers.mise import mise_exec


def run_with_mise(*command: str) -> str:
    completed = subprocess.run(
        mise_exec(*command),
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout


def skip_unless(requirement: Requirement) -> pytest.MarkDecorator:
    return pytest.mark.skipif(
        not requirement.is_met(), reason=f"needs {requirement.description}"
    )


@final
class RecordingContext:
    """An `UpdateContext` that records the commands of an update step."""

    def __init__(self, *, answers: bool = True) -> None:
        self.bump_versions: bool = False
        self.may_use_sudo: bool = True
        self.answers: bool = answers
        self.nothing_staged: bool = False
        self.commands: list[list[str]] = []
        self.environments: list[Mapping[str, str] | None] = []

    def section(self, _title: str, /) -> None:
        pass

    def confirm(self, _question: str, /) -> bool:
        return self.answers

    def note(self, _message: str, /) -> None:
        pass

    def succeeds(
        self, command: Sequence[str], *, working_directory: Path | None = None
    ) -> bool:
        del working_directory
        self.commands.append(list(command))
        return self.nothing_staged

    def run(
        self,
        command: Sequence[str],
        *,
        working_directory: Path | None = None,
        environment: Mapping[str, str] | None = None,
    ) -> None:
        del working_directory
        self.commands.append(list(command))
        self.environments.append(environment)
