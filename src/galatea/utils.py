"""Shared utility functions."""


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
