"""Marc module for Galatea."""
from typing import Union, Dict

__all__ = ['MarcEntryDataTypes', 'Marc_Entry']

MarcEntryDataTypes = Union[str, None]
Marc_Entry = Dict[str, MarcEntryDataTypes]
