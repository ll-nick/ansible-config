from devstack.testing import run_with_mise


def test_zoxide_runs() -> None:
    assert run_with_mise("zoxide", "--version").strip()
