import subprocess

from devstack.mise import mise_executable


def run_with_mise(*command: str) -> str:
    completed = subprocess.run(
        [str(mise_executable()), "exec", "--", *command],
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout
