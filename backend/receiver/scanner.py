"""Receiver scanner coordinating tuning calculations and bandwidth limits."""
from backend.shared.models import ScanRequest, ScanWindow
from backend.receiver.models import ReceiverConfig


class ReceiverScanner:
    """Calculates scan frequency boundaries and timing windows."""

    def __init__(self, config: ReceiverConfig):
        self.config = config

    def build_scan_window(
        self,
        request: ScanRequest,
        current_sim_time: float
    ) -> ScanWindow:
        """Construct the concrete ScanWindow for a given ScanRequest.

        Calculates frequency_end_hz = frequency_start_hz + bandwidth_hz.
        Calculates time_end = time_start + dwell_time_sec.
        """
        # Ensure bandwidth adheres to receiver hardware limit if not specified
        bw = request.bandwidth_hz or self.config.instantaneous_bandwidth_hz
        # Instantaneous bandwidth constraint (e.g. 500 MHz maximum)
        effective_bw = min(bw, self.config.instantaneous_bandwidth_hz)

        dwell_ms = request.dwell_time_ms or self.config.default_dwell_time_ms
        dwell_sec = dwell_ms / 1000.0

        freq_start = request.frequency_start_hz
        freq_end = freq_start + effective_bw

        time_start = round(current_sim_time, 6)
        time_end = round(time_start + dwell_sec, 6)

        return ScanWindow(
            frequency_start_hz=freq_start,
            frequency_end_hz=freq_end,
            dwell_time_ms=dwell_ms,
            time_start=time_start,
            time_end=time_end,
        )
