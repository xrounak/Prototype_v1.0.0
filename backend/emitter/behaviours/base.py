"""Base interface for emitter transmission behaviour strategies."""
from abc import ABC, abstractmethod
from typing import List
from backend.emitter.models import EmitterConfig, EmissionEvent


class BaseBehaviour(ABC):
    """Abstract strategy for generating emission events over a simulation time window."""

    @abstractmethod
    def generate(
        self,
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
            List of EmissionEvents.
        """
        pass

    @staticmethod
    def create_event(
        emitter: EmitterConfig,
        event_id: str,
        timestamp: float,
        time_end: float,
        freq_start: float,
        freq_end: float,
        duration_us: float,
        power_dbm: float,
        behavior_name: str,
        sequence_number: int = 0,
    ) -> EmissionEvent:
        """Helper to create standardized EmissionEvent with emitter metadata."""
        modulation_type = "UNMODULATED"
        if emitter.modulation and emitter.modulation.type:
            modulation_type = emitter.modulation.type

        return EmissionEvent(
            type="EMISSION_EVENT",
            event_id=event_id,
            emitter_id=emitter.emitter_id,
            timestamp=round(timestamp, 6),
            time_end=round(time_end, 6),
            emitter_category=emitter.category,
            emitter_subtype=emitter.subtype,
            frequency_start_hz=freq_start,
            frequency_end_hz=freq_end,
            bandwidth_hz=freq_end - freq_start,
            duration_us=round(duration_us, 2),
            power_dbm=power_dbm,
            behavior=behavior_name,
            modulation=modulation_type,
            sequence_number=sequence_number,
        )
