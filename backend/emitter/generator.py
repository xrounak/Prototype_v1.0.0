"""Emission event generator based on simulation time and emitter behavior."""
import math
from typing import List
from backend.shared.models import BehaviorType, EmitterConfig, EmissionEvent


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
            emitter: Emitter configuration parameters.
            time_start: Start of simulation window (seconds).
            time_end: End of simulation window (seconds).
        """
        if not emitter.active or time_end <= time_start:
            return []

        events: List[EmissionEvent] = []
        half_bw = emitter.bandwidth_hz / 2.0
        freq_start = emitter.frequency_hz - half_bw
        freq_end = emitter.frequency_hz + half_bw
        duration_sec = emitter.pulse_duration_us / 1_000_000.0

        if emitter.behavior_type == BehaviorType.CONTINUOUS:
            # Emits continuously across the entire requested interval
            event = EmissionEvent(
                event_id=f"{emitter.emitter_id}-CONT-{int(time_start * 1000)}",
                emitter_id=emitter.emitter_id,
                timestamp=round(time_start, 6),
                time_end=round(time_end, 6),
                frequency_start_hz=freq_start,
                frequency_end_hz=freq_end,
                duration_us=round((time_end - time_start) * 1_000_000.0, 2),
                power_dbm=emitter.power_dbm,
                behavior=emitter.behavior_type.value,
            )
            events.append(event)

        elif emitter.behavior_type == BehaviorType.PERIODIC:
            interval_sec = emitter.repetition_interval_ms / 1000.0
            if interval_sec <= 0:
                interval_sec = 0.05

            # Find all pulse indices k where pulse interval overlaps [time_start, time_end]
            # Pulse k starts at k * interval_sec
            k_min = max(0, int(math.floor((time_start - duration_sec) / interval_sec)))
            k_max = int(math.ceil(time_end / interval_sec)) + 1

            for k in range(k_min, k_max):
                p_start = k * interval_sec
                p_end = p_start + duration_sec
                # Check overlap with [time_start, time_end]
                if p_end >= time_start and p_start <= time_end:
                    event = EmissionEvent(
                        event_id=f"{emitter.emitter_id}-P{k}",
                        emitter_id=emitter.emitter_id,
                        timestamp=round(p_start, 6),
                        time_end=round(p_end, 6),
                        frequency_start_hz=freq_start,
                        frequency_end_hz=freq_end,
                        duration_us=emitter.pulse_duration_us,
                        power_dbm=emitter.power_dbm,
                        behavior=emitter.behavior_type.value,
                    )
                    events.append(event)

        elif emitter.behavior_type == BehaviorType.BURST:
            # Burst of `burst_count` pulses repeating every `repetition_interval_ms`
            interval_sec = emitter.repetition_interval_ms / 1000.0
            if interval_sec <= 0:
                interval_sec = 0.05
            intra_pulse_spacing = duration_sec * 2.0  # spacing within burst

            k_min = max(0, int(math.floor((time_start - (emitter.burst_count * intra_pulse_spacing)) / interval_sec)))
            k_max = int(math.ceil(time_end / interval_sec)) + 1

            for k in range(k_min, k_max):
                burst_start = k * interval_sec
                for b in range(emitter.burst_count):
                    p_start = burst_start + (b * intra_pulse_spacing)
                    p_end = p_start + duration_sec
                    if p_end >= time_start and p_start <= time_end:
                        event = EmissionEvent(
                            event_id=f"{emitter.emitter_id}-B{k}-{b}",
                            emitter_id=emitter.emitter_id,
                            timestamp=round(p_start, 6),
                            time_end=round(p_end, 6),
                            frequency_start_hz=freq_start,
                            frequency_end_hz=freq_end,
                            duration_us=emitter.pulse_duration_us,
                            power_dbm=emitter.power_dbm,
                            behavior=emitter.behavior_type.value,
                        )
                        events.append(event)

        return events
