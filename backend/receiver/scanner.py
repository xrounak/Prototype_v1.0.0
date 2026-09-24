"""Receiver scanner coordinating tuning calculations and bandwidth limits."""
from backend.shared.models import ScanRequest, ScanWindow
from backend.receiver.models import ReceiverConfig


class ReceiverScanner:
    """Calculates scan frequency boundaries and timing windows with validation."""

    def __init__(self, config: ReceiverConfig):
        self.config = config

    def validate_request(self, request: ScanRequest) -> float:
        """Validate tuning parameters against receiver hardware limits.

        Returns:
            effective_bw: clamped instantaneous bandwidth in Hz.
        """
        if request.frequency_start_hz < self.config.min_frequency_hz:
            raise ValueError(
                f"Requested start frequency {request.frequency_start_hz / 1e6:.1f} MHz is below "
                f"receiver minimum {self.config.min_frequency_hz / 1e6:.1f} MHz"
            )

        if request.frequency_start_hz >= self.config.max_frequency_hz:
            raise ValueError(
                f"Requested start frequency {request.frequency_start_hz / 1e6:.1f} MHz exceeds "
                f"receiver maximum {self.config.max_frequency_hz / 1e6:.1f} MHz"
            )

        # Enforce receiver instantaneous bandwidth limit
        requested_bw = request.bandwidth_hz if (request.bandwidth_hz and request.bandwidth_hz > 0) else self.config.instantaneous_bandwidth_hz
        effective_bw = min(requested_bw, self.config.instantaneous_bandwidth_hz)

        freq_end = request.frequency_start_hz + effective_bw
        if freq_end > self.config.max_frequency_hz:
            raise ValueError(
                f"Scan window end frequency {freq_end / 1e6:.1f} MHz exceeds "
                f"receiver maximum {self.config.max_frequency_hz / 1e6:.1f} MHz"
            )

        return effective_bw

    def build_scan_window(
        self,
        request: ScanRequest,
        current_sim_time: float
    ) -> ScanWindow:
        """Construct the concrete ScanWindow for a given ScanRequest.

        Validates tuning parameters and calculates frequency_end_hz and time_end.
        """
        effective_bw = self.validate_request(request)

        dwell_ms = request.dwell_time_ms if (request.dwell_time_ms and request.dwell_time_ms > 0) else self.config.default_dwell_time_ms
        dwell_sec = dwell_ms / 1000.0

        freq_start = request.frequency_start_hz
        freq_end = freq_start + effective_bw

        time_start = round(current_sim_time, 6)
        time_end = round(time_start + dwell_sec, 6)

        return ScanWindow(
            action_id=request.action_id,
            frequency_start_hz=freq_start,
            frequency_end_hz=freq_end,
            dwell_time_ms=dwell_ms,
            time_start=time_start,
            time_end=time_end,
        )
