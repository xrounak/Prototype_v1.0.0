"""Emission event generator delegating to modular behaviour strategies."""
from typing import List
from backend.emitter.models import EmitterConfig, EmissionEvent
from backend.emitter.behaviours import get_behaviour_strategy


class EmissionEventGenerator:
    """Generates emission events for emitters across simulation time windows."""

    @staticmethod
    def generate_events_for_emitter(
        emitter: EmitterConfig,
        time_start: float,
        time_end: float
    ) -> List[EmissionEvent]:
        """Generate all emissions produced by `emitter` in the interval [time_start, time_end].

        Args:
            emitter: Emitter configuration and profiles.
            time_start: Start of simulation window (seconds).
            time_end: End of simulation window (seconds).

        Returns:
            List of generated EmissionEvents.
        """
        if not emitter.active or time_end <= time_start:
            return []

        strategy = get_behaviour_strategy(emitter.behavior.type)
        return strategy.generate(emitter, time_start, time_end)
