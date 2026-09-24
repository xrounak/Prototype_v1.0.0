"""Periodic pulsed transmission behaviour."""
import math
from typing import List
from backend.emitter.models import EmitterConfig, EmissionEvent
from backend.emitter.behaviours.base import BaseBehaviour


class PeriodicBehaviour(BaseBehaviour):
    """Generates regular pulsed emissions at constant pulse repetition interval (PRI)."""

    def generate(
        self,
        emitter: EmitterConfig,
        time_start: float,
        time_end: float
    ) -> List[EmissionEvent]:
        if time_end <= time_start:
            return []

        events: List[EmissionEvent] = []
        half_bw = emitter.rf.bandwidth_hz / 2.0
        freq_start = emitter.rf.center_frequency_hz - half_bw
        freq_end = emitter.rf.center_frequency_hz + half_bw
        duration_sec = max(1e-7, emitter.behavior.pulse_width_us / 1_000_000.0)

        interval_sec = emitter.behavior.repetition_interval_ms / 1000.0
        if interval_sec <= 0:
            interval_sec = 0.05

        k_min = max(0, int(math.floor((time_start - duration_sec) / interval_sec)))
        k_max = int(math.ceil(time_end / interval_sec)) + 1

        for k in range(k_min, k_max):
            p_start = k * interval_sec
            p_end = p_start + duration_sec
            if p_end >= time_start and p_start <= time_end:
                events.append(
                    self.create_event(
                        emitter=emitter,
                        event_id=f"{emitter.emitter_id}-P{k}",
                        timestamp=p_start,
                        time_end=p_end,
                        freq_start=freq_start,
                        freq_end=freq_end,
                        duration_us=emitter.behavior.pulse_width_us,
                        power_dbm=emitter.rf.power_dbm,
                        behavior_name="PERIODIC",
                        sequence_number=k,
                    )
                )

        return events
