from devstack.testing import run_with_mise


def test_ripgrep_runs() -> None:
    assert run_with_mise("rg", "--version").strip()
