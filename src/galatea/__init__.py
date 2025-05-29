# noqa: D104
import logging as _logging
from . import tsv

__all__ = ["tsv"]

VERBOSE_LEVEL_NUM = 15
_logging.addLevelName(VERBOSE_LEVEL_NUM, "VERBOSE")
