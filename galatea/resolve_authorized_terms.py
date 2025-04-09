"""Resolve unauthorized terms to authorized terms in a tsv file."""

import collections
import functools
import logging
import pathlib
from typing import Optional, TypedDict, Iterable
import galatea.tsv
import galatea.marc

__all__ = ['DEFAULT_TRANSFORMATION_FILE_NAME', 'resolve_authorized_terms']

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


TransformationData = TypedDict(
    "TransformationData",
    {
        "unauthorized term": str,
        "resolving authorized term": str,
    },
)

DEFAULT_TRANSFORMATION_FILE_NAME = "authorized_terms_transformation.tsv"


class Transform(collections.abc.Mapping):
    dialect = "excel-tab"

    def __init__(self, fp):
        self._fp = fp

    @classmethod
    @functools.cache
    def locate_in_file(cls, fp, key: str) -> Optional[str]:
        rows: Iterable[galatea.tsv.TableRow[TransformationData]] = (
            galatea.tsv.iter_tsv_fp(fp, dialect=cls.dialect)
        )
        for row in rows:
            if row.entry["unauthorized term"] == key:
                return row.entry["resolving authorized term"]
        return None

    def __getitem__(self, key):
        value = self.locate_in_file(self._fp, key)
        if value is None:
            raise KeyError(key)
        return value

    def __len__(self):
        rows = 0
        for _ in galatea.tsv.iter_tsv_fp(self._fp, dialect=self.dialect):
            rows += 1
        return rows

    def __iter__(self):
        """Iterate over the entries in the transformation file."""
        for row in galatea.tsv.iter_tsv_fp(self._fp, dialect=self.dialect):
            yield row.entry


default_resolved_fields = {"260$a", "264$a"}


def resolve_authorized_terms(
    input_tsv: pathlib.Path,
    transformation_file: pathlib.Path,
    output_file: pathlib.Path,
) -> None:
    """Resolve unauthorized terms to authorized terms in found tsv file."""
    new_data = []

    with transformation_file.open("r") as fp:
        transformer = Transform(fp)

        rows: Iterable[galatea.tsv.TableRow[galatea.marc.Marc_Entry]] = (
            galatea.tsv.iter_tsv_file(input_tsv, dialect="excel-tab")
        )
        for row in rows:
            new_row = row.entry.copy()

            for field in default_resolved_fields:
                if values := row.entry[field]:
                    values = values.strip()
                    if not values:
                        continue
                    new_values = []
                    for value in values.split("||"):
                        if transformation := transformer.get(value):
                            new_values.append(transformation.strip())
                        else:
                            new_values.append(value)

                    new_row[field] = "||".join(new_values)
                    # entry_differ = difflib.Differ()
                    # res = entry_differ.compare([str(new_row[field])], [str(row.entry[field])])
                    # print("-"* 80)
                    # print("\n".join(res))
            new_data.append(new_row)
    with output_file.open("w") as fp:
        galatea.tsv.write_tsv_fp(fp, data=new_data, dialect="excel-tab")
    logger.info(f"Wrote to {output_file.name}")


def create_init_transformation_file(output: pathlib.Path):
    """Create a new transformation file with the header."""
    logger.debug("creating new transformation tsv file")
    if output.exists():
        raise FileExistsError(output.absolute())

    with output.open("w") as fp:
        fp.write("unauthorized term\tresolving authorized term\n")
    logger.info(f"Wrote new transformation tsv file to {output.absolute()}")
    return None
