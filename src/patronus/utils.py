from abc import ABC, abstractmethod
from threading import Lock

from typing import Optional, Callable, Any
import warnings

NOT_GIVEN = object()


class LogSerializer(ABC):
    """
    Abstract base class for objects that can serialize themselves for logging.

    Classes implementing this interface provide a method to convert their state
    into a dictionary format suitable for OpenTelemetry logging.
    """

    @abstractmethod
    def dump_as_log(self) -> Any:
        """
        Serialize the object into a dictionary format suitable for logging.

        Returns:
            A dictionary representation of the object for logging purposes.
        """
        pass


def merge_tags(tags: Optional[dict], new_tags: Optional[dict], experiment_tags: Optional[dict]) -> dict:
    # Avoid creating extra dicts/sets and dictionary unpacking
    tags = tags or {}
    new_tags = new_tags or {}
    experiment_tags = experiment_tags or {}

    # Mutate a copy so original 'tags' is not altered (behaviorally preserved)
    merged_tags = tags.copy()
    merged_tags.update(new_tags)

    # Use set intersection directly and check only overlapping keys
    diff = [k for k in experiment_tags if k in merged_tags and merged_tags[k] != experiment_tags[k]]
    if diff:
        warnings.warn(f"Overriding experiment tags is not allowed. Tried to override tag: {diff!r}")

    # Overlay experiment_tags on top (experiment_tags take precedence)
    result = merged_tags.copy()
    result.update(experiment_tags)
    return result


class Once:
    # Execute a function exactly once and block all callers until the function returns
    #
    # Same as golang's `sync.Once <https://pkg.go.dev/sync#Once>`_

    def __init__(self) -> None:
        self._lock = Lock()
        self._done = False

    def do_once(self, func: Callable[[], None]) -> bool:
        # Execute ``func`` if it hasn't been executed or return.
        #
        # Will block until ``func`` has been called by one thread.
        #
        # Returns:
        #     Whether ``func`` was executed in this call

        # fast path, try to avoid locking
        if self._done:
            return False

        with self._lock:
            if not self._done:
                func()
                self._done = True
                return True
        return False
