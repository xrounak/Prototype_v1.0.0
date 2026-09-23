"""Emitter Service and Environment Manager.

Maintains emitters in the environment and provides clean decoupled queries
for receiver observation calculation.
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
    """Manages active emitter profiles and scenarios."""

    def __init__(self):
        self._emitters: Dict[str, EmitterConfig] = {}
        self._load_default_emitters()

    def _load_default_emitters(self) -> None:
        """Initialize baseline radar/emitter environment."""
        defaults = [
            EmitterConfig(
                emitter_id="E001",
                name="S-Band Acquisition Radar",
                frequency_hz=930_000_000.0,  # 930 MHz
                bandwidth_hz=10_000_000.0,   # 10 MHz
                power_dbm=30.0,
                pulse_duration_us=250.0,
                repetition_interval_ms=50.0,
                burst_count=3,
                behavior_type=BehaviorType.BURST,
                active=True,
            ),
            EmitterConfig(
                emitter_id="E002",
                name="Airborne Intercept Radar",
                frequency_hz=1_150_000_000.0,  # 1.15 GHz
                bandwidth_hz=20_000_000.0,    # 20 MHz
                power_dbm=42.0,
                pulse_duration_us=120.0,
                repetition_interval_ms=25.0,
                behavior_type=BehaviorType.PERIODIC,
                active=True,
            ),
            EmitterConfig(
                emitter_id="E003",
                name="Continuous Wave Illuminator",
                frequency_hz=850_000_000.0,  # 850 MHz
                bandwidth_hz=5_000_000.0,    # 5 MHz
                power_dbm=25.0,
                pulse_duration_us=1000.0,
                repetition_interval_ms=10.0,
                behavior_type=BehaviorType.CONTINUOUS,
                active=True,
            ),
        ]
        for em in defaults:
            self._emitters[em.emitter_id] = em

    def get_all_emitters(self) -> List[EmitterConfig]:
        """Return all registered emitters."""
        return list(self._emitters.values())

    def get_emitter(self, emitter_id: str) -> Optional[EmitterConfig]:
        """Get an emitter by ID."""
        return self._emitters.get(emitter_id)

    def add_or_update_emitter(self, emitter: EmitterConfig) -> None:
        """Register or update an emitter."""
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

    def __init__(self, manager: Optional[EmitterManager] = None, event_bus: Optional[EventBus] = None):
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

            # First, check if emitter frequency band overlaps the receiver window
            half_bw = emitter.bandwidth_hz / 2.0
            em_f_start = emitter.frequency_hz - half_bw
            em_f_end = emitter.frequency_hz + half_bw

            # Overlap check: [em_f_start, em_f_end] overlaps [frequency_start_hz, frequency_end_hz]
            if em_f_end < frequency_start_hz or em_f_start > frequency_end_hz:
                continue

            # Generate all temporal emissions for this emitter during this time slice
            events = EmissionEventGenerator.generate_events_for_emitter(
                emitter, time_start_sec, time_end_sec
            )
            matched_emissions.extend(events)

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
                logger.info(f"[{event.timestamp:.3f}] EMITTER {event.emitter_id} generated emission ({event.behavior})")
                await self.event_bus.publish(
                    EventMessage(
                        type="EMISSION_EVENT",
                        timestamp=event.timestamp,
                        payload=event.model_dump(),
                    )
                )

        return all_events
