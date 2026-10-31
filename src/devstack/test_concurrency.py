import gevent

from devstack.concurrency import run_all


def test_run_all_never_exceeds_the_limit() -> None:
    running = 0
    peak = 0

    def task() -> int:
        nonlocal running, peak
        running += 1
        peak = max(peak, running)
        gevent.sleep(0.01)
        running -= 1
        return 1

    results = run_all([task] * 8, limit=3)

    assert results == [1] * 8
    assert peak == 3
