from devstack.testing import run_with_mise


def test_lazygit_runs() -> None:
    assert run_with_mise("lazygit", "--version").strip()
