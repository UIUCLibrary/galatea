"""Shared utility functions."""

from importlib import metadata
from typing import Optional


class GalateaException(Exception):
    """Galatea exception."""


class CommandFinishedWithException(GalateaException):
    """Command was able to complete but there are were issues.

    Example usage of this would be:
        a tsv file needed to merge all rows. All but one row was successful.
        Instead of exiting at this point with a partially written file, the
        command finished the remaining rows. Even though the process was a
         failure, the other data was written to the file successfully.
        Perhaps this single row might be able to manually entered by the user,
        so we want to keep the remaining data.
        However, the entire process was NOT a success.
    """


def get_versions_from_package() -> Optional[str]:
    """Get version information from the package metadata."""
    if not __package__:
        return None

    try:
        return metadata.version(__package__)
    except metadata.PackageNotFoundError:
        return None


DEFAULT_VERSION_STRATEGIES = [get_versions_from_package]


def get_version() -> str:
    """Get the version of current application."""
    for strategy in DEFAULT_VERSION_STRATEGIES:
        version = strategy()
        if version:
            return version
    return "unknown version"
