from devstack.testing import run_with_mise


def test_fd_runs() -> None:
    assert run_with_mise("fd", "--version").startswith("fd ")
