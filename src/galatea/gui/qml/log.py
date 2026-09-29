"""Configure Qt and Python logging."""

import sys

from PySide6 import QtCore
import logging


class LogSignalHandler(logging.Handler):
    """A logging handler that emits log messages to a Qt signal."""

    def __init__(self, signal: QtCore.SignalInstance, level: int = 0) -> None:
        """Configure a logging handler.

        Args:
            signal: signal with a single string argument to emit messages to.
            level: logging level to filter messages by.
        """
        super().__init__(level)
        self.signal = signal

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log message to given qt signal."""
        self.signal.emit(self.format(record))


def qt_message_handler(
    logger: logging.Logger,
    mode: QtCore.QtMsgType,
    context: QtCore.QMessageLogContext,
    message: str,
    include_context=False,
):
    """Configure Qt messages and pass them to a Python logger."""
    context_info = f" [{context.file}:{context.line}]" if context.file else ""
    if include_context:
        full_message = f"{message}{context_info}"
    else:
        full_message = message
    match mode:
        case QtCore.QtMsgType.QtDebugMsg:
            logger.debug(full_message)
        case QtCore.QtMsgType.QtInfoMsg:
            logger.info(full_message)
        case QtCore.QtMsgType.QtWarningMsg:
            logger.warning("QML Warning: %s", full_message)
        case QtCore.QtMsgType.QtCriticalMsg:
            logger.critical("QML Critical: %s", full_message)
        case QtCore.QtMsgType.QtFatalMsg:
            logger.fatal("QML Fatal: %s", full_message)
            sys.exit(1)
        case _:
            logger.error("QML Error: %s", full_message)
