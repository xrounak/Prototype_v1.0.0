"""Jittered pulse repetition interval (PRI) behaviour."""
import hashlib
import math
from typing import List
from backend.emitter.models import EmitterConfig, EmissionEvent
from backend.emitter.behaviours.base import BaseBehaviour


class JitteredBehaviour(BaseBehaviour):
    """Generates pulses with intentionally jittered PRIs to counter deinterleaving."""

    def _get_jitter_offset(self, emitter_id: str, k: int, base_pri_sec: float, jitter_pct: float) -> float:
        """Deterministic pseudo-random jitter offset for pulse index k."""
        key = f"{emitter_id}:jit:{k}".encode("utf-8")
        h = int(hashlib.md5(key).hexdigest()[:8], 16)
        # Normalize to [-1.0, 1.0]
        norm = (h / 0x7FFFFFFF) - 1.0
        max_offset = base_pri_sec * (jitter_pct / 100.0)
        return norm * max_offset

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

        base_pri_sec = (emitter.behavior.base_pri_ms or emitter.behavior.repetition_interval_ms or 25.0) / 1000.0
        if base_pri_sec <= 0:
            base_pri_sec = 0.025

        jitter_pct = emitter.behavior.jitter_percent or 5.0
        max_jitter_sec = base_pri_sec * (jitter_pct / 100.0)

        # Estimate search window over k
        k_min = max(0, int(math.floor((time_start - max_jitter_sec - duration_sec) / base_pri_sec)))
        k_max = int(math.ceil((time_end + max_jitter_sec) / base_pri_sec)) + 1

        for k in range(k_min, k_max):
            offset = self._get_jitter_offset(emitter.emitter_id, k, base_pri_sec, jitter_pct)
            p_start = k * base_pri_sec + offset
            if p_start < 0:
                p_start = 0.0
            p_end = p_start + duration_sec

            if p_end >= time_start and p_start <= time_end:
                events.append(
                    self.create_event(
                        emitter=emitter,
                        event_id=f"{emitter.emitter_id}-JIT-{k}",
                        timestamp=p_start,
                        time_end=p_end,
                        freq_start=freq_start,
                        freq_end=freq_end,
                        duration_us=emitter.behavior.pulse_width_us,
                        power_dbm=emitter.rf.power_dbm,
                        behavior_name="JITTERED",
                        sequence_number=k,
                    )
                )

        return events
