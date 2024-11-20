"""Manipulated tsv files."""

from typing import (
    TextIO,
    Union,
    Type,
    Protocol,
    Iterable,
    Callable,
    TypeVar,
    Mapping, Sequence
)
import csv
import logging
import pathlib
import contextlib
from collections.abc import Iterator

logger = logging.getLogger(__name__)

T = TypeVar("T")

__all__ = [
    "iter_tsv_fp",
    "iter_tsv_file",
    "get_tsv_dialect",
    "write_tsv_fp",
    "write_tsv_file",
]


@contextlib.contextmanager
def remembered_file_pointer_head(fp: TextIO) -> Iterator[TextIO]:
    starting = fp.tell()
    try:
        yield fp
    finally:
        fp.seek(starting)


def iter_tsv_fp(
    fp: TextIO, dialect: Union[Type[csv.Dialect], csv.Dialect]
) -> Iterable[T]:
    """Iterate over tsv lines from a file-like object.

    Args:
        fp: file-pointer object.
        dialect: the dialect to use.

    Yields:
        Dictionary containing a row from the tsv file.

    """
    with remembered_file_pointer_head(fp):
        yield from csv.DictReader(fp, dialect=dialect)


def iter_tsv_file(
    file_name: pathlib.Path,
    dialect: Union[Type[csv.Dialect], csv.Dialect],
    strategy: Callable[
        [TextIO, Union[Type[csv.Dialect], csv.Dialect]], Iterable[T]
    ] = iter_tsv_fp,
) -> Iterable[T]:
    """Iterate over tsv lines from file found at path given.

    Args:
        file_name: file path to open.
        dialect: tsv dialect to use.
        strategy: tsv reader strategy.

    Yields:
        Dictionary containing a row from the tsv file.

    """
    with open(file_name, newline="", encoding="utf8") as tsv_file:
        yield from strategy(tsv_file, dialect)


class DetectionStrategy(Protocol):
    def __call__(self, fp: TextIO) -> Union[Type[csv.Dialect], csv.Dialect]:
        """Detect the dialect of a tsv file.

        if unable to figure it out, the function throws a DialectDetectionError
        """


class UnknownDialect(Exception):
    """Unable to detect tsv dialect."""


def _sniff_tsv_dialect(fp: TextIO) -> Union[Type[csv.Dialect], csv.Dialect]:
    with remembered_file_pointer_head(fp):
        try:
            sniffer = csv.Sniffer()
            return sniffer.sniff(fp.read(1024 * 2), delimiters="\t")
        except csv.Error as e:
            raise UnknownDialect() from e


def get_tsv_dialect(
    fp: TextIO, detection_strategy: DetectionStrategy = _sniff_tsv_dialect
) -> Union[Type[csv.Dialect], csv.Dialect]:
    """Get a tsv dialect from a file-like object.

    Args:
        fp: file-pointer object to a tsv file.
        detection_strategy: strategy to use to detect the dialect.

    Returns:
        Dialect of the tsv file or throws UnknownDialect if unable to detect.

    """
    with remembered_file_pointer_head(fp):
        try:
            return detection_strategy(fp)
        except UnknownDialect as e:
            logger.warning(
                'Using "excel-tab" for tsv dialect due to unknown tsv '
                "dialect. Reason: %s",
                e,
            )
            return csv.get_dialect("excel-tab")


def write_tsv_fp(
    fp: TextIO,
    data: Sequence[Mapping[str, Union[str, None]]],
    dialect: Union[Type[csv.Dialect], csv.Dialect],
) -> None:
    """Write data to a file-pointer.

    Args:
        fp: file-pointer object to a tsv file.
        data: data to write.
        dialect: tsv dialect to use.

    """
    try:
        fieldnames = data[0].keys()
    except IndexError:
        logger.warning("No tsv data written.")
        return
    writer = csv.DictWriter(fp, fieldnames=fieldnames, dialect=dialect)
    writer.writeheader()
    for row in data:
        writer.writerow(row)


def write_tsv_file(
    file_name: pathlib.Path,
    data: Sequence[Mapping[str, Union[str, None]]],
    dialect: Union[Type[csv.Dialect], csv.Dialect],
    writing_strategy: Callable[
        [TextIO, Sequence[Mapping[str, Union[str, None]]], Union[Type[csv.Dialect], csv.Dialect]],
        None,
    ] = write_tsv_fp
) -> None:
    """Write data to a file at given path.

    Args:
        file_name: file path to write to.
        data: data to write.
        dialect: tsv dialect to use.
        writing_strategy: writing strategy to use.

    """
    with open(file_name, "w", newline="", encoding="utf8") as tsv_file:
        writing_strategy(tsv_file, data, dialect)
