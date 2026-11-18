import pytest

pytest.importorskip("galatea.gui.qml")


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "fail_immediately(reason): skip execution and mark the test as FAILED",
    )


def pytest_runtest_setup(item):
    mark = item.get_closest_marker("fail_immediately")
    if mark:
        reason = mark.kwargs.get("reason") or (
            mark.args[0] if mark.args else "Marked to fail without execution"
        )
        pytest.fail(reason, pytrace=False)
