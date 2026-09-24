"""Frequency hopping transmission behaviour."""
import math
from typing import List
from backend.emitter.models import EmitterConfig, EmissionEvent
from backend.emitter.behaviours.base import BaseBehaviour


class FrequencyHoppingBehaviour(BaseBehaviour):
    """Generates emissions that switch discrete carrier frequencies across time."""

    def generate(
        self,
        emitter: EmitterConfig,
        time_start: float,
        time_end: float
    ) -> List[EmissionEvent]:
        if time_end <= time_start:
            return []

        hops = emitter.behavior.hop_frequencies_hz
        if not hops:
            base_f = emitter.rf.center_frequency_hz
            hops = [base_f - 40e6, base_f - 20e6, base_f + 20e6, base_f + 40e6]

        dwell_sec = (emitter.behavior.dwell_time_ms or 50.0) / 1000.0
        if dwell_sec <= 0:
            dwell_sec = 0.05

        events: List[EmissionEvent] = []
        half_bw = emitter.rf.bandwidth_hz / 2.0
        duration_sec = max(1e-7, emitter.behavior.pulse_width_us / 1_000_000.0)
        pri_sec = (emitter.behavior.repetition_interval_ms or 25.0) / 1000.0

        # Check if pulsed or continuous dwell
        is_pulsed = pri_sec > 0 and pri_sec < dwell_sec * 5

        if is_pulsed:
            k_min = max(0, int(math.floor((time_start - duration_sec) / pri_sec)))
            k_max = int(math.ceil(time_end / pri_sec)) + 1

            for k in range(k_min, k_max):
                p_start = k * pri_sec
                p_end = p_start + duration_sec

                if p_end >= time_start and p_start <= time_end:
                    hop_idx = int(math.floor(p_start / dwell_sec)) % len(hops)
                    center_f = hops[hop_idx]
                    f_start = center_f - half_bw
                    f_end = center_f + half_bw

                    events.append(
                        self.create_event(
                            emitter=emitter,
                            event_id=f"{emitter.emitter_id}-HOP-{k}",
                            timestamp=p_start,
                            time_end=p_end,
                            freq_start=f_start,
                            freq_end=f_end,
                            duration_us=emitter.behavior.pulse_width_us,
                            power_dbm=emitter.rf.power_dbm,
                            behavior_name="FREQUENCY_HOPPING",
                            sequence_number=k,
                        )
                    )
        else:
            # Continuous dwell blocks
            h_min = max(0, int(math.floor(time_start / dwell_sec)))
            h_max = int(math.ceil(time_end / dwell_sec)) + 1

            for h in range(h_min, h_max):
                d_start = h * dwell_sec
                d_end = d_start + dwell_sec

                if d_end >= time_start and d_start <= time_end:
                    # Clip to query window
                    w_start = max(time_start, d_start)
                    w_end = min(time_end, d_end)
                    center_f = hops[h % len(hops)]
                    f_start = center_f - half_bw
                    f_end = center_f + half_bw

                    events.append(
                        self.create_event(
                            emitter=emitter,
                            event_id=f"{emitter.emitter_id}-HOP-{h}",
                            timestamp=w_start,
                            time_end=w_end,
                            freq_start=f_start,
                            freq_end=f_end,
                            duration_us=(w_end - w_start) * 1_000_000.0,
                            power_dbm=emitter.rf.power_dbm,
                            behavior_name="FREQUENCY_HOPPING",
                            sequence_number=h,
                        )
                    )

        return events
