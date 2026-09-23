"""Lightweight asynchronous in-memory Event Bus.

Facilitates decoupled communication between:
- Emitter Service -> Gateway
- Receiver Service -> Gateway
- Simulation Controller -> Services
"""
import asyncio
import logging
from typing import Any, Callable, Coroutine, Dict, List
from backend.shared.models import EventMessage

logger = logging.getLogger("ew.eventbus")

HandlerFunc = Callable[[EventMessage], Coroutine[Any, Any, None]]


class EventBus:
    """Async publish-subscribe event dispatcher."""

    def __init__(self):
        self._subscribers: Dict[str, List[HandlerFunc]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, event_type: str, handler: HandlerFunc) -> None:
        """Register a handler callback for an event type (or '*' for all events)."""
        async with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            if handler not in self._subscribers[event_type]:
                self._subscribers[event_type].append(handler)
        logger.debug(f"Subscribed handler {handler.__name__ if hasattr(handler, '__name__') else handler} to '{event_type}'")

    async def unsubscribe(self, event_type: str, handler: HandlerFunc) -> None:
        """Unregister a handler callback."""
        async with self._lock:
            if event_type in self._subscribers and handler in self._subscribers[event_type]:
                self._subscribers[event_type].remove(handler)

    async def publish(self, event_message: EventMessage) -> None:
        """Publish an event message to all relevant subscribers."""
        event_type = event_message.type

        handlers: List[HandlerFunc] = []
        async with self._lock:
            if event_type in self._subscribers:
                handlers.extend(self._subscribers[event_type])
            if "*" in self._subscribers:
                handlers.extend(self._subscribers["*"])

        if not handlers:
            return

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_message)
                else:
                    handler(event_message)
            except Exception as e:
                logger.error(f"Error in EventBus handler for event '{event_type}': {e}", exc_info=True)


# Global singleton instance for easy import across modules
global_event_bus = EventBus()
