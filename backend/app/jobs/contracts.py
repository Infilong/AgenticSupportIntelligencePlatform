from collections.abc import Callable
from dataclasses import dataclass


class RetryableJobError(Exception):
    """A temporary execution conflict that can use the existing bounded retry policy."""


@dataclass(frozen=True)
class Publication:
    """Perform a domain write inside the worker's authorized, fenced completion transaction."""

    publish: Callable
