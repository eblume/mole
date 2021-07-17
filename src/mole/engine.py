import logging
from typing import Optional

from .event_loop import EventLoop

log = logging.getLogger(__name__)


class Engine:
    _event_loop: Optional[EventLoop] = None

    @property
    def event_loop(self) -> EventLoop:
        if self._event_loop is None:
            log.debug("A new event loop is being created")
            self._event_loop = EventLoop()

        return self._event_loop

    def run_forever(self) -> None:
        """Run the engine in a loop 'forever', until a shutdown signal is received."""

        # Execute the event loop.
        self.event_loop.start()
