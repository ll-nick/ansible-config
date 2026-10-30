from devstack.testing import run_with_mise


def test_leadr_runs() -> None:
    assert run_with_mise("leadr", "--version").strip()
