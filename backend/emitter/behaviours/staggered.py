"""Staggered pulse repetition interval (PRI) behaviour."""
import math
from typing import List
from backend.emitter.models import EmitterConfig, EmissionEvent
from backend.emitter.behaviours.base import BaseBehaviour


class StaggeredBehaviour(BaseBehaviour):
    """Generates pulses that cycle through a repeating sequence of distinct PRIs."""

    def generate(
        self,
        emitter: EmitterConfig,
        time_start: float,
        time_end: float
    ) -> List[EmissionEvent]:
        if time_end <= time_start:
            return []

        seq_ms = emitter.behavior.pri_sequence_ms
        if not seq_ms:
            # Fallback to base PRI if sequence is empty
            pri_ms = emitter.behavior.repetition_interval_ms or 50.0
            seq_ms = [pri_ms, pri_ms * 1.4, pri_ms * 1.2]

        seq_sec = [ms / 1000.0 for ms in seq_ms]
        cycle_len = len(seq_sec)
        cycle_duration = sum(seq_sec)
        if cycle_duration <= 0:
            cycle_duration = 0.15

        events: List[EmissionEvent] = []
        half_bw = emitter.rf.bandwidth_hz / 2.0
        freq_start = emitter.rf.center_frequency_hz - half_bw
        freq_end = emitter.rf.center_frequency_hz + half_bw
        duration_sec = max(1e-7, emitter.behavior.pulse_width_us / 1_000_000.0)

        # Estimate cycle range
        c_min = max(0, int(math.floor((time_start - cycle_duration - duration_sec) / cycle_duration)))
        c_max = int(math.ceil(time_end / cycle_duration)) + 1

        for c in range(c_min, c_max):
            c_base = c * cycle_duration
            acc_time = 0.0
            for s in range(cycle_len):
                p_start = c_base + acc_time
                p_end = p_start + duration_sec
                k = c * cycle_len + s

                if p_end >= time_start and p_start <= time_end:
                    events.append(
                        self.create_event(
                            emitter=emitter,
                            event_id=f"{emitter.emitter_id}-STAG-{k}",
                            timestamp=p_start,
                            time_end=p_end,
                            freq_start=freq_start,
                            freq_end=freq_end,
                            duration_us=emitter.behavior.pulse_width_us,
                            power_dbm=emitter.rf.power_dbm,
                            behavior_name="STAGGERED",
                            sequence_number=k,
                        )
                    )

                acc_time += seq_sec[s]

        return events
