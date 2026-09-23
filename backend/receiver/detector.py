"""Receiver signal detection logic.

Evaluates frequency and temporal overlap between the receiver's current
scan dwell window and observed emission events from the emitter environment.
"""
import uuid
from typing import List
from backend.shared.models import Detection, EmissionEvent, ScanWindow


class ReceiverDetector:
    """Computes detections based on frequency and time overlap."""

    @staticmethod
    def evaluate_emissions(
        emissions: List[EmissionEvent],
        scan_window: ScanWindow,
        noise_floor_dbm: float = -95.0
    ) -> List[Detection]:
        """Convert overlapping emission events into receiver detections.

        Args:
            emissions: Emission events returned by the emitter environment.
            scan_window: The active scan frequency and time window.
            noise_floor_dbm: Detection sensitivity threshold.

        Returns:
            List of detected signal observations.
        """
        detections: List[Detection] = []

        for em in emissions:
            # 1. Frequency Overlap Check
            freq_overlap_start = max(scan_window.frequency_start_hz, em.frequency_start_hz)
            freq_overlap_end = min(scan_window.frequency_end_hz, em.frequency_end_hz)

            if freq_overlap_end <= freq_overlap_start:
                continue

            # 2. Temporal Overlap Check
            time_overlap_start = max(scan_window.time_start, em.timestamp)
            time_overlap_end = min(scan_window.time_end, em.time_end)

            if time_overlap_end <= time_overlap_start:
                continue

            # 3. Overlap Ratio calculation
            em_bandwidth = em.frequency_end_hz - em.frequency_start_hz
            overlap_bw = freq_overlap_end - freq_overlap_start
            overlap_ratio = min(1.0, max(0.0, overlap_bw / em_bandwidth if em_bandwidth > 0 else 1.0))

            # 4. Sensitivity threshold check
            if em.power_dbm < noise_floor_dbm:
                continue

            detection = Detection(
                detection_id=f"DET-{uuid.uuid4().hex[:8].upper()}",
                emitter_id=em.emitter_id,
                frequency_start_hz=freq_overlap_start,
                frequency_end_hz=freq_overlap_end,
                detected_power_dbm=em.power_dbm,
                timestamp=round(time_overlap_start, 6),
                duration_us=round((time_overlap_end - time_overlap_start) * 1_000_000.0, 2),
                overlap_ratio=round(overlap_ratio, 3),
            )
            detections.append(detection)

        return detections
