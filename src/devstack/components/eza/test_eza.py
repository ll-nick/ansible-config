from devstack.testing import run_with_mise


def test_eza_runs() -> None:
    assert run_with_mise("eza", "--version").strip()
