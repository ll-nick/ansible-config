from devstack.testing import run_with_mise


def test_node_and_pnpm_run() -> None:
    assert run_with_mise("node", "--version").strip()
    assert run_with_mise("pnpm", "--version").strip()
