from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Publication:
    """Perform a domain write inside the worker's authorized, fenced completion transaction."""

    publish: Callable
