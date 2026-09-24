"""Unit tests for receiver hardware validation, dwell window boundaries, and metadata preservation."""
import pytest
from backend.shared.models import ScanRequest, EmissionEvent
from backend.receiver.models import ReceiverConfig
from backend.receiver.scanner import ReceiverScanner
from backend.receiver.detector import ReceiverDetector


def test_receiver_scanner_frequency_limits_validation():
    """Verify ReceiverScanner enforces min and max hardware tuning boundaries."""
    cfg = ReceiverConfig(
        min_frequency_hz=500e6,
        max_frequency_hz=3000e6,
        instantaneous_bandwidth_hz=500e6,
    )
    scanner = ReceiverScanner(cfg)

    # 1. Tuning below minimum should fail
    with pytest.raises(ValueError, match="below receiver minimum"):
        scanner.build_scan_window(ScanRequest(action_id=1, frequency_start_hz=400e6), current_sim_time=0.0)

    # 2. Tuning above maximum should fail
    with pytest.raises(ValueError, match="exceeds receiver maximum"):
        scanner.build_scan_window(ScanRequest(action_id=2, frequency_start_hz=3100e6), current_sim_time=0.0)

    # 3. Tuning where end frequency exceeds max should fail
    with pytest.raises(ValueError, match="exceeds receiver maximum"):
        scanner.build_scan_window(ScanRequest(action_id=3, frequency_start_hz=2800e6, bandwidth_hz=500e6), current_sim_time=0.0)


def test_receiver_instantaneous_bandwidth_clamping():
    """Verify receiver clamps requested bandwidth to its hardware instantaneous capability."""
    cfg = ReceiverConfig(instantaneous_bandwidth_hz=500e6)
    scanner = ReceiverScanner(cfg)

    # Requesting 1000 MHz bandwidth should be clamped to 500 MHz
    req = ScanRequest(action_id=4, frequency_start_hz=1000e6, bandwidth_hz=1000e6)
    window = scanner.build_scan_window(req, current_sim_time=5.0)

    assert window.frequency_start_hz == 1000e6
    assert window.frequency_end_hz == 1500e6  # 1000 + 500 MHz limit
    assert window.dwell_time_ms == 25.0


def test_detector_overlap_and_metadata_retention():
    """Verify ReceiverDetector correctly computes overlap and preserves complete emitter metadata."""
    scanner = ReceiverScanner(ReceiverConfig())
    req = ScanRequest(action_id=5, frequency_start_hz=1000e6, bandwidth_hz=500e6, dwell_time_ms=25.0)
    scan_window = scanner.build_scan_window(req, current_sim_time=1.0)

    # Emission 1: inside frequency window [1100, 1120] and time [1.005, 1.010]
    em1 = EmissionEvent(
        event_id="EM-EV-1",
        emitter_id="RADAR-X",
        timestamp=1.005,
        time_end=1.010,
        emitter_category="RADAR",
        emitter_subtype="TRACKING",
        frequency_start_hz=1100e6,
        frequency_end_hz=1120e6,
        bandwidth_hz=20e6,
        duration_us=5000.0,
        power_dbm=38.0,
        behavior="PERIODIC",
        modulation="LFM",
    )

    # Emission 2: outside frequency window [600, 700]
    em2 = EmissionEvent(
        event_id="EM-EV-2",
        emitter_id="RADAR-OUT",
        timestamp=1.005,
        time_end=1.010,
        emitter_category="RADAR",
        frequency_start_hz=600e6,
        frequency_end_hz=700e6,
        bandwidth_hz=100e6,
        duration_us=5000.0,
        power_dbm=30.0,
        behavior="BURST",
    )

    # Emission 3: outside time window [1.050, 1.060] (dwell ends at 1.025)
    em3 = EmissionEvent(
        event_id="EM-EV-3",
        emitter_id="RADAR-LATE",
        timestamp=1.050,
        time_end=1.060,
        emitter_category="RADAR",
        frequency_start_hz=1100e6,
        frequency_end_hz=1120e6,
        bandwidth_hz=20e6,
        duration_us=10000.0,
        power_dbm=35.0,
        behavior="CONTINUOUS",
    )

    detections = ReceiverDetector.evaluate_emissions(
        emissions=[em1, em2, em3],
        scan_window=scan_window,
    )

    assert len(detections) == 1
    det = detections[0]
    assert det.emitter_id == "RADAR-X"
    assert det.emitter_category == "RADAR"
    assert det.emitter_subtype == "TRACKING"
    assert det.behaviour == "PERIODIC"
    assert det.modulation == "LFM"
    assert det.detected_power_dbm == 38.0
    assert det.frequency_start_hz == 1100e6
    assert det.frequency_end_hz == 1120e6
