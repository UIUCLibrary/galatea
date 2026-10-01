import sys

import pytest
import logging
from unittest.mock import Mock

QtCore = pytest.importorskip("PySide6.QtCore")
log = pytest.importorskip("galatea.gui.qml.log")


@pytest.mark.parametrize(
    "mode, log_level, expected_args",
    [
        (QtCore.QtMsgType.QtDebugMsg, "debug", ["test"]),
        (QtCore.QtMsgType.QtInfoMsg, "info", ["test"]),
        (
            QtCore.QtMsgType.QtWarningMsg,
            "warning",
            ["QML Warning: %s", "test"],
        ),
        (
            QtCore.QtMsgType.QtCriticalMsg,
            "critical",
            ["QML Critical: %s", "test"],
        ),
        (
            QtCore.QtMsgType.QtFatalMsg,
            "fatal",
            ["QML Fatal: %s", "test"],
        ),
        (
            -1,
            "error",
            ["QML Error: %s", "test"],
        ),
    ],
)
def test_qt_message_handler(monkeypatch, mode, log_level, expected_args):
    logger = Mock(spec_set=logging.Logger)
    monkeypatch.setattr(sys, "exit", Mock())
    log.qt_message_handler(
        logger=logger, mode=mode, context=Mock(), message="test"
    )
    getattr(logger, log_level).assert_called_once_with(*expected_args)


class TestLogSignalHandler:
    def test_emit(self):
        class Dummy(QtCore.QObject):
            log_signal = QtCore.Signal(str)

            def __init__(self):
                super().__init__()
                self.logged_message = []
                self.log_signal.connect(self.logged_message.append)

        dummy = Dummy()
        handler = log.LogSignalHandler(dummy.log_signal)

        logger = logging.getLogger(__name__)
        logger.addHandler(handler)
        logger.error("test")

        assert dummy.logged_message == ["test"]
