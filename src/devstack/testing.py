import subprocess

import pytest

from devstack.component import Requirement
from devstack.mise import mise_executable


def run_with_mise(*command: str) -> str:
    completed = subprocess.run(
        [str(mise_executable()), "exec", "--", *command],
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout


def skip_unless(requirement: Requirement) -> pytest.MarkDecorator:
    return pytest.mark.skipif(
        not requirement.is_met(), reason=f"needs {requirement.description}"
    )
