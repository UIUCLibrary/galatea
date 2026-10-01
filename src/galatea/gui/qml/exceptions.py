"""QML Gui related exception."""

from typing import Optional, List
from PySide6 import QtQml
from galatea.utils import GalateaException


class QMLException(GalateaException):
    """QML based exception."""


class QMLLoadingError(QMLException):
    """Exception raised when there is an error loading QML files."""

    def __init__(  # noqa: D107
        self,
        file: str,
        errors: Optional[List[QtQml.QQmlError]] = None,
        *args: object,
    ) -> None:
        super().__init__(*args)
        self.file = file
        self.errors = errors or []

    def __str__(self) -> str:  # noqa: D105
        errors = []
        for error in self.errors:
            errors.append(
                f"QML Component error: "
                f"{error.url().toString()}:{error.line()}:{error.column()}: "
                f"{error.description()}"
            )
        details = "\n".join(errors)
        return f"Error loading QML file {self.file}: {details}"
