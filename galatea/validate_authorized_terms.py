"""Validate authorized terms."""

import abc
import collections.abc
import logging
import pathlib
import time
from typing import Dict, Callable, Iterator, TypeVar, Generic, Iterable
from urllib.parse import quote

import requests

from galatea.tsv import iter_tsv_file, get_tsv_dialect

__all__ = ["validate_authorized_terms"]

API_REQUEST_RATE_LIMIT_IN_SECONDS = 0.1

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

T = TypeVar("T")


class AbsCachedCheck(collections.abc.Container[str], abc.ABC, Generic[T]):
    # def __init__(self, requesting_strategy: Callable[[str], T]) -> None:
    def __init__(self) -> None:
        self.data_cache: Dict[str, T] = {}

    @abc.abstractmethod
    def request_data(self, key: str) -> T:
        """Request data for a key.

        This method should be used by when the value is not cached already.

        Do not use this outside of implementing the concrete class.

        This will make a request but will not check cache nor will it cache the
        response.
        """

    def get_data(self, key: str) -> T:
        if key in self.data_cache:
            logger.debug("reusing cached value for %s", key)
            return self.data_cache[key]
        logger.debug("fetching data from %s", key)
        self.data_cache[key] = self.request_data(key)
        return self.data_cache[key]

    def clear_cache(self) -> None:
        self.data_cache.clear()

    def __contains__(self, key: object) -> bool:
        return key in self.data_cache


class CachedApiCheck(AbsCachedCheck[requests.Response]):
    default_request_strategy = requests.get

    def __init__(
        self,
        requesting_strategy: Callable[
            [str], requests.Response
        ] = default_request_strategy,
    ) -> None:
        super().__init__()
        self._request_strategy = requesting_strategy

    def request_data(self, key: str) -> requests.Response:
        return self._request_strategy(key)


class NameCheck(CachedApiCheck):
    def __contains__(self, key: object) -> bool:
        if isinstance(key, str):
            return super().__contains__(self._get_url(key))
        else:
            return super().__contains__(key)

    @staticmethod
    def _get_url(name: str) -> str:
        return f"https://id.loc.gov/authorities/names/label/{quote(name)}"

    def get_data(self, key: str) -> requests.Response:
        return super().get_data(self._get_url(key))


def check_terms(name: str, cache: CachedApiCheck) -> bool:
    return cache.get_data(name).status_code == 200


def optional_rate_limited_iterator(
    iterable: Iterable[T],
    bypass_sleep_func: Callable[[T], bool] = lambda *_: False,
    max_time: float = API_REQUEST_RATE_LIMIT_IN_SECONDS,
    sleep_func: Callable[[float],None] = time.sleep
) -> Iterator[T]:
    """Iterate over a generator and time limit the rate of yield.

    Args:
        iterable: Iterable to iterate over
        bypass_sleep_func: optional callback function to determine if the
            wait before the next iteration can be bypassed
        max_time: Maximum wait time in seconds before yielding another
            iteration
        sleep_func: Optional sleep function used.

    Yields: results of generator_func

    """
    start_time = time.time()
    for i, results in enumerate(iterable):
        if i> 0 and not bypass_sleep_func(results):
                elapsed_time = time.time() - start_time
                if elapsed_time < max_time:
                    sleep_func(max_time - elapsed_time)
                    start_time = time.time()
        yield results


class IterTerms(collections.abc.Iterable):
    tsv_file_row_iterator = iter_tsv_file

    def __init__(self, source):
        self._source = source
        self.field_names = set()

    def iter_rows(self):
        with open(self._source, encoding="utf-8") as tsv_file:
            dialect = get_tsv_dialect(tsv_file)
        for row in IterTerms.tsv_file_row_iterator(self._source, dialect):
            yield row

    def __iter__(self):
        for row in self.iter_rows():
            for field_name in self.field_names:
                field = row.entry[field_name]
                if not field:
                    continue
                field = field.strip()
                for name in field.split("||"):
                    cleaned_string = name.strip()
                    yield row.line_number, field_name, cleaned_string


def validate_authorized_terms(source: pathlib.Path) -> None:
    """Validate Authorized terms.

    Args:
        source: Marc tsv file to validate

    """
    logger.info("validating authorized terms")
    checker = NameCheck()
    terms_to_check = IterTerms(source)
    terms_to_check.field_names.add("260$a")
    terms_to_check.field_names.add("264$a")
    for (
        line_number,
        field_name,
        value,
    ) in optional_rate_limited_iterator(
        terms_to_check,
        bypass_sleep_func=lambda results: results[2] in checker,
    ):
        result = check_terms(value, checker)
        if result is False:
            logger.info(
                f'Line: {line_number} | Field: "{field_name}" | "{value}" is not an authorized term.'
            )
