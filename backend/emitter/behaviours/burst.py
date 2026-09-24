"""Burst transmission behaviour."""
import math
from typing import List
from backend.emitter.models import EmitterConfig, EmissionEvent
from backend.emitter.behaviours.base import BaseBehaviour


class BurstBehaviour(BaseBehaviour):
    """Generates groups of pulses (bursts) repeating at defined burst intervals."""

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

        # Main burst repetition period
        burst_interval_sec = (emitter.behavior.burst_interval_ms or 500.0) / 1000.0
        if burst_interval_sec <= 0:
            burst_interval_sec = 0.5

        # Intra-burst spacing (between pulses within one burst)
        intra_sec = (emitter.behavior.repetition_interval_ms or 20.0) / 1000.0
        if intra_sec <= duration_sec:
            intra_sec = duration_sec * 2.0

        burst_count = max(1, emitter.behavior.burst_count)
        burst_span_sec = (burst_count - 1) * intra_sec + duration_sec

        k_min = max(0, int(math.floor((time_start - burst_span_sec) / burst_interval_sec)))
        k_max = int(math.ceil(time_end / burst_interval_sec)) + 1

        for k in range(k_min, k_max):
            burst_start = k * burst_interval_sec
            for b in range(burst_count):
                p_start = burst_start + (b * intra_sec)
                p_end = p_start + duration_sec
                if p_end >= time_start and p_start <= time_end:
                    events.append(
                        self.create_event(
                            emitter=emitter,
                            event_id=f"{emitter.emitter_id}-B{k}-{b}",
                            timestamp=p_start,
                            time_end=p_end,
                            freq_start=freq_start,
                            freq_end=freq_end,
                            duration_us=emitter.behavior.pulse_width_us,
                            power_dbm=emitter.rf.power_dbm,
                            behavior_name="BURST",
                            sequence_number=k * 100 + b,
                        )
                    )

        return events
