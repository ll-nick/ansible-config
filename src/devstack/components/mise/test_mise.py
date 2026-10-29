import subprocess

from devstack.mise import mise_executable


def test_mise_runs() -> None:
    completed = subprocess.run(
        [str(mise_executable()), "--version"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert completed.stdout.strip()
