"""Shared validator code."""

from typing import List, Optional
from speedwagon import validators
from speedwagon.workflow import UserData

__all__ = ["ValidateFileExtension", "ValidateValueIsNotEmpty"]


class ValidateFileExtension(validators.AbsOutputValidation[str, str]):
    """Validate that a file has the correct extension."""

    def __init__(self, extension: str) -> None:
        """Initialize the validator class with given extension.

        Args:
            extension: The required file extension.
        """
        super().__init__()
        self.extension = extension

    def investigate(
        self, candidate: Optional[str], job_options: UserData
    ) -> List[str]:
        """Investigate if the value has the correct file extension."""
        if candidate and not candidate.endswith(self.extension):
            return [f"File must be a {self.extension} file"]
        return []


class ValidateValueIsNotEmpty(validators.AbsOutputValidation[str, str]):
    """Validate that a value is not empty."""

    def investigate(
        self, candidate: Optional[str], job_options: UserData
    ) -> List[str]:
        """Investigate if the value is not empty."""
        if not candidate:
            return ["Value is empty"]
        return []
