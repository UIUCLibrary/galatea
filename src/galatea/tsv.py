"""TSV file related code."""

import contextlib
import csv
import dataclasses
import logging
import pathlib
import typing

from typing import (
    Callable,
    Generic,
    List,
    TextIO,
    TypeVar,
    Union,
    Iterator,
    Iterable,
    Optional,
    Protocol,
    Type,
)

from galatea.marc import Marc_Entry

__all__ = [
    "get_field_names",
    "TableRow",
    "iter_tsv_file",
    "UnknownDialect",
    "get_tsv_dialect",
    "get_field_names",
    "get_field_names_fp",
    "write_tsv_file",
    "write_tsv_fp",
]

T = TypeVar("T")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@contextlib.contextmanager
def remembered_file_pointer_head(fp: TextIO) -> Iterator[TextIO]:
    starting = fp.tell()
    try:
        yield fp
    finally:
        fp.seek(starting)


@dataclasses.dataclass(frozen=True)
class TableRow(Generic[T]):
    """Table row."""

    line_number: int
    entry: T


def iter_tsv_fp(
    fp: TextIO, dialect: Union[Type[csv.Dialect], csv.Dialect, str]
) -> Iterable[TableRow[T]]:
    with remembered_file_pointer_head(fp):
        reader = csv.DictReader(fp, dialect=dialect)
        for row in reader:
            yield TableRow(
                line_number=reader.line_num,
                entry=typing.cast(T, row)
            )


def iter_tsv_file(
    file_name: pathlib.Path,
    dialect: Union[Type[csv.Dialect], csv.Dialect],
    strategy: Callable[
        [TextIO, Union[Type[csv.Dialect], csv.Dialect]],
        Iterable[TableRow[T]],
    ] = iter_tsv_fp,
) -> Iterable[TableRow[T]]:
    """Iterate over entries in a given tsv file.

    Args:
        file_name: file path to tsv to use,
        dialect: dialect of tsv file
        strategy: function to read tsv to file pointer

    Yields: data

    """
    with open(file_name, newline="", encoding="utf8") as tsv_file:
        yield from strategy(tsv_file, dialect)


def write_tsv_fp(
    fp: TextIO,
    data: List[Marc_Entry],
    dialect: Union[Type[csv.Dialect], csv.Dialect],
) -> None:
    """Write tsv file to file pointer.

    Args:
        fp: file pointer opened with write mode
        data: rows of marc data
        dialect: dialect of tsv file to use

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
    data: List[Marc_Entry],
    dialect: Union[Type[csv.Dialect], csv.Dialect],
    writing_strategy: Callable[
        [TextIO, List[Marc_Entry], Union[Type[csv.Dialect], csv.Dialect]],
        None,
    ] = write_tsv_fp,
) -> None:
    """Write tsv file to file with given name.

    Args:
        file_name: path to file use for saving
        data: Rows of Marc data to save
        dialect: Dialect of tsv file to use
        writing_strategy: function to write tsv file to an open file pointer

    """
    with open(file_name, "w", newline="", encoding="utf8") as tsv_file:
        writing_strategy(tsv_file, data, dialect)


class UnknownDialect(Exception):
    """Unable to detect tsv dialect."""


class DetectionStrategy(Protocol):
    def __call__(self, fp: TextIO) -> Union[Type[csv.Dialect], csv.Dialect]:
        """Detect the dialect of a tsv file.

        if unable to figure it out, the function throws a DialectDetectionError
        """


def _sniff_tsv_dialect(fp: TextIO) -> Union[Type[csv.Dialect], csv.Dialect]:
    with remembered_file_pointer_head(fp):
        try:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(fp.read(1024 * 2), delimiters="\t")
            if dialect.doublequote is False:
                logger.warning(
                    f"dialog deterimined by {_sniff_tsv_dialect.__name__} using "
                    f"double quotes, dispite not detected them in source tsv "
                    f"file."
                )
                dialect.doublequote = True
            return dialect
        except csv.Error as e:
            raise UnknownDialect() from e


def get_tsv_dialect(
    fp: TextIO, detection_strategy: DetectionStrategy = _sniff_tsv_dialect
) -> Union[Type[csv.Dialect], csv.Dialect]:
    """Attempt to identify the dialect of a tsv file pointer.

    Args:
        fp: file pointer to a tsv file.
        detection_strategy: detection strategy function

    Returns: tsv dialect best guess.

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
            return csv.get_dialect("excel-tab")  # type:ignore[return-value]


def get_field_names_fp(
    fp: TextIO, dialect: Union[Type[csv.Dialect], csv.Dialect]
):
    """Get field names of tsv from a file pointer.

    Args:
        fp: open file pointer
        dialect: tsv dialect

    Returns: List of field names

    """
    fieldnames = csv.DictReader(fp, dialect=dialect).fieldnames
    if fieldnames is None:
        raise ValueError("file contains no field names")
    return list(fieldnames)


def get_field_names(
    file_name: pathlib.Path,
    dialect: Optional[Union[Type[csv.Dialect], csv.Dialect]] = None,
    strategy: Callable[
        [TextIO, Union[Type[csv.Dialect], csv.Dialect]], List[str]
    ] = get_field_names_fp,
) -> List[str]:
    """Get field names of tsv.

    Args:
        file_name: path to tsv file
        dialect: tsv dialect
        strategy: function for getting field names from a file pointer

    Returns: List of field names

    """
    with open(file_name, newline="", encoding="utf-8") as tsv_file:
        return strategy(tsv_file, dialect or get_tsv_dialect(tsv_file))
