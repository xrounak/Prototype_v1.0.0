"""Frequency agile transmission behaviour."""
import hashlib
import math
from typing import List
from backend.emitter.models import EmitterConfig, EmissionEvent
from backend.emitter.behaviours.base import BaseBehaviour


class FrequencyAgileBehaviour(BaseBehaviour):
    """Generates emissions whose carrier frequency agility varies within a bounded frequency band."""

    def _get_agile_frequency(
        self,
        emitter_id: str,
        interval_idx: int,
        min_f: float,
        max_f: float
    ) -> float:
        """Deterministic carrier frequency selection for agile interval."""
        key = f"{emitter_id}:agile:{interval_idx}".encode("utf-8")
        h = int(hashlib.md5(key).hexdigest()[:8], 16)
        ratio = (h % 10000) / 10000.0
        return min_f + ratio * (max_f - min_f)

    def generate(
        self,
        emitter: EmitterConfig,
        time_start: float,
        time_end: float
    ) -> List[EmissionEvent]:
        if time_end <= time_start:
            return []

        min_f = emitter.behavior.min_frequency_hz
        max_f = emitter.behavior.max_frequency_hz
        if min_f <= 0 or max_f <= min_f:
            center_f = emitter.rf.center_frequency_hz
            span = emitter.rf.bandwidth_hz * 5.0
            min_f = center_f - span
            max_f = center_f + span

        change_interval_sec = (emitter.behavior.change_interval_ms or 25.0) / 1000.0
        if change_interval_sec <= 0:
            change_interval_sec = 0.025

        events: List[EmissionEvent] = []
        half_bw = emitter.rf.bandwidth_hz / 2.0
        duration_sec = max(1e-7, emitter.behavior.pulse_width_us / 1_000_000.0)
        pri_sec = (emitter.behavior.repetition_interval_ms or 30.0) / 1000.0
        if pri_sec <= 0:
            pri_sec = 0.030

        k_min = max(0, int(math.floor((time_start - duration_sec) / pri_sec)))
        k_max = int(math.ceil(time_end / pri_sec)) + 1

        for k in range(k_min, k_max):
            p_start = k * pri_sec
            p_end = p_start + duration_sec

            if p_end >= time_start and p_start <= time_end:
                interval_idx = int(math.floor(p_start / change_interval_sec))
                center_f = self._get_agile_frequency(emitter.emitter_id, interval_idx, min_f, max_f)
                f_start = center_f - half_bw
                f_end = center_f + half_bw

                events.append(
                    self.create_event(
                        emitter=emitter,
                        event_id=f"{emitter.emitter_id}-AGILE-{k}",
                        timestamp=p_start,
                        time_end=p_end,
                        freq_start=f_start,
                        freq_end=f_end,
                        duration_us=emitter.behavior.pulse_width_us,
                        power_dbm=emitter.rf.power_dbm,
                        behavior_name="FREQUENCY_AGILE",
                        sequence_number=k,
                    )
                )

        return events
