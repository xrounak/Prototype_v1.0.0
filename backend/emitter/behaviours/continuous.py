"""Continuous wave / continuous transmission behaviour."""
from typing import List
from backend.emitter.models import EmitterConfig, EmissionEvent
from backend.emitter.behaviours.base import BaseBehaviour


class ContinuousBehaviour(BaseBehaviour):
    """Generates continuous emission covering the entire simulation interval."""

    def generate(
        self,
        emitter: EmitterConfig,
        time_start: float,
        time_end: float
    ) -> List[EmissionEvent]:
        if time_end <= time_start:
            return []

        half_bw = emitter.rf.bandwidth_hz / 2.0
        freq_start = emitter.rf.center_frequency_hz - half_bw
        freq_end = emitter.rf.center_frequency_hz + half_bw
        duration_us = (time_end - time_start) * 1_000_000.0

        event_id = f"{emitter.emitter_id}-CONT-{int(time_start * 1000)}"
        event = self.create_event(
            emitter=emitter,
            event_id=event_id,
            timestamp=time_start,
            time_end=time_end,
            freq_start=freq_start,
            freq_end=freq_end,
            duration_us=duration_us,
            power_dbm=emitter.rf.power_dbm,
            behavior_name="CONTINUOUS",
            sequence_number=int(time_start * 1000),
        )
        return [event]
