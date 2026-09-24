"""Emitter Service and Generic Emitter Manager.

Maintains active emitters and provides clean decoupled queries
for receiver observation calculation and real-time event broadcasting.
"""
import logging
from typing import Dict, List, Optional
from backend.shared.models import (
    BehaviorType,
    EmitterConfig,
    EmissionEvent,
    EventMessage,
)
from backend.shared.events import EventBus, global_event_bus
from backend.emitter.generator import EmissionEventGenerator

logger = logging.getLogger("ew.emitter")


class EmitterManager:
    """Manages active emitter profiles generically without hard-coded populations."""

    def __init__(self, initial_emitters: Optional[List[EmitterConfig]] = None):
        self._emitters: Dict[str, EmitterConfig] = {}
        if initial_emitters:
            self.load_emitters(initial_emitters)

    def load_emitters(self, emitters: List[EmitterConfig]) -> None:
        """Replace the current emitter population with a new list of emitters."""
        self._emitters.clear()
        for em in emitters:
            self._emitters[em.emitter_id] = em
        logger.info(f"Loaded {len(self._emitters)} emitters into EmitterManager.")

    def clear(self) -> None:
        """Clear all active emitters."""
        self._emitters.clear()

    def get_all_emitters(self) -> List[EmitterConfig]:
        """Return all registered emitters."""
        return list(self._emitters.values())

    def get_emitter(self, emitter_id: str) -> Optional[EmitterConfig]:
        """Get an emitter by ID."""
        return self._emitters.get(emitter_id)

    def add_or_update_emitter(self, emitter: EmitterConfig) -> None:
        """Register or update an emitter profile."""
        self._emitters[emitter.emitter_id] = emitter

    def remove_emitter(self, emitter_id: str) -> bool:
        """Remove an emitter from the environment."""
        return self._emitters.pop(emitter_id, None) is not None

    def set_active(self, emitter_id: str, active: bool) -> bool:
        """Toggle active state of a specific emitter."""
        if emitter_id in self._emitters:
            self._emitters[emitter_id].active = active
            return True
        return False


class EmitterService:
    """Service that coordinates emitter generation and environment queries."""

    def __init__(
        self,
        manager: Optional[EmitterManager] = None,
        event_bus: Optional[EventBus] = None
    ):
        self.manager = manager or EmitterManager()
        self.event_bus = event_bus or global_event_bus
        self.is_running: bool = True

    def start(self) -> None:
        """Start emitter service."""
        self.is_running = True
        logger.info("Emitter service started.")

    def stop(self) -> None:
        """Stop emitter service."""
        self.is_running = False
        logger.info("Emitter service stopped.")

    def query_emissions_in_window(
        self,
        frequency_start_hz: float,
        frequency_end_hz: float,
        time_start_sec: float,
        time_end_sec: float
    ) -> List[EmissionEvent]:
        """Clean decoupled interface queried by the receiver.

        Returns all emission events that occurred within [time_start_sec, time_end_sec]
        and overlap in frequency with [frequency_start_hz, frequency_end_hz].
        """
        if not self.is_running:
            return []

        matched_emissions: List[EmissionEvent] = []
        for emitter in self.manager.get_all_emitters():
            if not emitter.active:
                continue

            # Generate all temporal emissions for this emitter during this time slice
            events = EmissionEventGenerator.generate_events_for_emitter(
                emitter, time_start_sec, time_end_sec
            )

            # Filter events that overlap with requested frequency window
            for event in events:
                if event.frequency_end_hz >= frequency_start_hz and event.frequency_start_hz <= frequency_end_hz:
                    matched_emissions.append(event)

        return matched_emissions

    async def step_and_publish(self, time_start_sec: float, time_end_sec: float) -> List[EmissionEvent]:
        """Simulate a time step across all emitters and publish emissions to EventBus."""
        if not self.is_running:
            return []

        all_events: List[EmissionEvent] = []
        for emitter in self.manager.get_all_emitters():
            if not emitter.active:
                continue

            events = EmissionEventGenerator.generate_events_for_emitter(
                emitter, time_start_sec, time_end_sec
            )
            for event in events:
                all_events.append(event)
                logger.debug(f"[{event.timestamp:.3f}] EMITTER {event.emitter_id} generated emission ({event.behavior})")
                await self.event_bus.publish(
                    EventMessage(
                        type="EMISSION_EVENT",
                        timestamp=event.timestamp,
                        payload=event.model_dump(),
                    )
                )

        return all_events
