from devstack.testing import run_with_mise


def test_fzf_runs() -> None:
    assert run_with_mise("fzf", "--version").strip()
