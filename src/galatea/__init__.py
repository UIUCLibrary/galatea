"""Galatea package.

.. versionadded:: 0.4.0
    module `galatea.merge_data` added

.. versionadded:: 0.3.1
    module `galatea.resolve_authorized_terms` &
    `galatea.validate_authorized_terms` added.

"""
# noqa: D104
import logging as _logging
from . import tsv

__all__ = ["tsv"]

VERBOSE_LEVEL_NUM = 15
_logging.addLevelName(VERBOSE_LEVEL_NUM, "VERBOSE")
