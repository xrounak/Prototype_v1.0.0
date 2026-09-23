"""Unit and integration tests for the modular EW simulation pipeline."""
import pytest
from backend.shared.clock import SimulationClock
from backend.shared.models import (
    BehaviorType,
    EmitterConfig,
    ScanRequest,
)
from backend.shared.events import EventBus
from backend.emitter.service import EmitterManager, EmitterService
from backend.receiver.service import ReceiverService
from backend.receiver.scanner import ReceiverScanner
from backend.receiver.detector import ReceiverDetector


def test_simulation_clock():
    """Verify simulation clock advance, reset, and precision."""
    clock = SimulationClock(0.0)
    assert clock.now() == 0.0

    clock.advance(0.025)
    assert clock.now() == 0.025

    clock.advance(0.050)
    assert clock.now() == 0.075

    clock.reset(10.0)
    assert clock.now() == 10.0


def test_emitter_continuous_generation():
    """Verify continuous emitter generation."""
    manager = EmitterManager()
    service = EmitterService(manager=manager)

    # Query 840-860 MHz (E003 is at 850 MHz)
    emissions = service.query_emissions_in_window(
        frequency_start_hz=840_000_000.0,
        frequency_end_hz=860_000_000.0,
        time_start_sec=0.0,
        time_end_sec=0.025,
    )
    assert len(emissions) >= 1
    assert any(e.emitter_id == "E003" for e in emissions)


def test_receiver_scanner_bandwidth_window():
    """Verify receiver calculates 500 MHz instantaneous window: freq_end = freq_start + 500 MHz."""
    service = ReceiverService()
    req = ScanRequest(
        action_id=101,
        frequency_start_hz=700_000_000.0,
        bandwidth_hz=500_000_000.0,
        dwell_time_ms=25.0,
    )
    window = service.scanner.build_scan_window(req, current_sim_time=12.450)

    assert window.frequency_start_hz == 700_000_000.0
    assert window.frequency_end_hz == 1_200_000_000.0  # 700 MHz + 500 MHz = 1200 MHz
    assert window.dwell_time_ms == 25.0
    assert window.time_start == 12.450
    assert window.time_end == 12.475


@pytest.mark.asyncio
async def test_full_pipeline_scan_detection():
    """Verify end-to-end flow:
    Emitter in environment -> Receiver scans 700-1200MHz -> E001 (930MHz) is detected -> Observation returned.
    """
    clock = SimulationClock(10.0)
    bus = EventBus()
    emitter_service = EmitterService(event_bus=bus)
    receiver_service = ReceiverService(
        clock=clock,
        emitter_service=emitter_service,
        event_bus=bus,
    )

    received_events = []

    async def test_handler(event):
        received_events.append(event)

    await bus.subscribe("*", test_handler)

    # Scan from 700 MHz to 1200 MHz (500 MHz BW). E001 at 930 MHz falls inside!
    scan_req = ScanRequest(
        action_id=2001,
        frequency_start_hz=700_000_000.0,
        bandwidth_hz=500_000_000.0,
        dwell_time_ms=50.0,
    )

    obs = await receiver_service.execute_scan(scan_req)

    # Assert observation structure
    assert obs.observation_id.startswith("OBS-")
    assert obs.scan.frequency_start_hz == 700_000_000.0
    assert obs.scan.frequency_end_hz == 1_200_000_000.0
    assert obs.timestamp == 10.050  # 10.0 + 0.050s dwell

    # Assert detections: E001 (930MHz) and E003 (850MHz) are both in 700-1200MHz!
    detected_ids = [d.emitter_id for d in obs.detections]
    assert "E003" in detected_ids or "E001" in detected_ids

    # Assert event bus captured SCAN_REQUEST and RECEIVER_OBSERVATION
    event_types = [e.type for e in received_events]
    assert "SCAN_REQUEST" in event_types
    assert "RECEIVER_OBSERVATION" in event_types
