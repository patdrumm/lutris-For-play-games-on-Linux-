from typing import Callable, Dict, List, Tuple

from lutris.util.jobs import schedule_at_idle


class NotificationSource:
    """A class to inform interested code of changes in a global, like a signal but not attached to any
    object."""

    def __init__(self) -> None:
        self._generation_number = 0
        self._callbacks: Dict[int, Callable] = {}
        self._next_callback_id = 1
        self._scheduled_callbacks: List[Tuple[Callable, Tuple, Dict]] = []

    def fire(self, *args, **kwargs) -> None:
        """Signals that the thing, whatever it is, has happened. This increments the generation number,
        and schedules the callbacks to run (if they are not scheduled already)."""
        self._generation_number += 1
        for callback in self._callbacks.values():
            self._scheduled_callbacks.append((callback, args, kwargs))
        schedule_at_idle(self._notify)

    @property
    def generation_number(self) -> int:
        """Returns a number that is incremented on each call to fire(). This can be polled
        passively, when registering a callback is inappropriate."""
        return self._generation_number

    def register(self, callback: Callable) -> int:
        """Registers a callback to be called after the thing, whatever it is, has happened;
        fire() schedules callbacks to be called at idle time on the main thread.

        Note that a callback will be kept alive until unregistered, and this can keep
        large objects alive until then.

        Returns an id number to use to unregister the callback."""
        callback_id = self._next_callback_id
        self._callbacks[callback_id] = callback
        self._next_callback_id += 1
        return callback_id

    def unregister(self, callback_id: int) -> None:
        """Unregisters a callback that register() had registered."""
        self._callbacks.pop(callback_id, None)

    def _notify(self):
        while self._scheduled_callbacks:
            callback, args, kwargs = self._scheduled_callbacks.pop(0)
            callback(*args, **kwargs)
