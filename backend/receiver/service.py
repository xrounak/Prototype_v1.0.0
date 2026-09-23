"""Receiver Service.

Manages receiver hardware state, executes scan commands, queries the emitter
environment via a clean decoupled interface, and generates observations.
"""
import logging
import uuid
from typing import Optional
from backend.shared.models import (
    EventMessage,
    Observation,
    ScanRequest,
)
from backend.shared.clock import SimulationClock
from backend.shared.events import EventBus, global_event_bus
from backend.receiver.models import ReceiverConfig, ReceiverState
from backend.receiver.scanner import ReceiverScanner
from backend.receiver.detector import ReceiverDetector
from backend.emitter.service import EmitterService

logger = logging.getLogger("ew.receiver")


class ReceiverService:
    """Coordinates receiver tuning, environment queries, and observation outputs."""

    def __init__(
        self,
        config: Optional[ReceiverConfig] = None,
        clock: Optional[SimulationClock] = None,
        emitter_service: Optional[EmitterService] = None,
        event_bus: Optional[EventBus] = None,
    ):
        self.config = config or ReceiverConfig()
        self.state = ReceiverState(receiver_id=self.config.receiver_id)
        self.scanner = ReceiverScanner(self.config)
        self.detector = ReceiverDetector()
        self.clock = clock
        self.emitter_service = emitter_service
        self.event_bus = event_bus or global_event_bus
        self.is_running: bool = True

    def start(self) -> None:
        """Start the receiver service."""
        self.is_running = True
        self.state.status = "IDLE"
        logger.info("Receiver service started.")

    def stop(self) -> None:
        """Stop the receiver service."""
        self.is_running = False
        self.state.status = "STOPPED"
        logger.info("Receiver service stopped.")

    async def execute_scan(self, request: ScanRequest) -> Observation:
        """Execute a receiver scan dwell over the specified frequency window.

        Workflow:
        1. Calculate frequency window (freq_end = freq_start + 500 MHz) and dwell duration.
        2. Publish SCAN_REQUEST event to EventBus.
        3. Query decoupled emitter environment for overlapping emissions.
        4. Detect signals and advance simulation clock by dwell time.
        5. Generate Observation and broadcast RECEIVER_OBSERVATION to EventBus.
        """
        if not self.is_running:
            raise RuntimeError("Receiver service is currently stopped.")

        sim_time = self.clock.now() if self.clock else 0.0
        scan_window = self.scanner.build_scan_window(request, sim_time)

        self.state.status = "SCANNING"
        self.state.current_scan_window = scan_window

        # Structured log: Receiver started scan
        logger.info(
            f"[{scan_window.time_start:.3f}] RECEIVER started scan "
            f"({scan_window.frequency_start_hz / 1e6:.1f} MHz -> {scan_window.frequency_end_hz / 1e6:.1f} MHz, "
            f"dwell={scan_window.dwell_time_ms:.1f}ms)"
        )

        # Broadcast SCAN_REQUEST event to gateway/frontend
        await self.event_bus.publish(
            EventMessage(
                type="SCAN_REQUEST",
                timestamp=scan_window.time_start,
                payload={
                    "action_id": request.action_id,
                    "frequency_start_hz": scan_window.frequency_start_hz,
                    "frequency_end_hz": scan_window.frequency_end_hz,
                    "bandwidth_hz": scan_window.frequency_end_hz - scan_window.frequency_start_hz,
                    "dwell_time_ms": scan_window.dwell_time_ms,
                    "time_start": scan_window.time_start,
                    "time_end": scan_window.time_end,
                }
            )
        )

        # 3. Query decoupled emitter environment
        emissions = []
        if self.emitter_service:
            emissions = self.emitter_service.query_emissions_in_window(
                frequency_start_hz=scan_window.frequency_start_hz,
                frequency_end_hz=scan_window.frequency_end_hz,
                time_start_sec=scan_window.time_start,
                time_end_sec=scan_window.time_end,
            )

        # 4. Evaluate detections
        detections = self.detector.evaluate_emissions(
            emissions=emissions,
            scan_window=scan_window,
            noise_floor_dbm=self.config.noise_floor_dbm,
        )

        # Advance simulation clock if clock is attached
        if self.clock:
            dwell_sec = scan_window.dwell_time_ms / 1000.0
            self.clock.advance(dwell_sec)
            completion_time = self.clock.now()
        else:
            completion_time = scan_window.time_end

        # Structured logs
        logger.info(f"[{completion_time:.3f}] RECEIVER completed scan")
        logger.info(f"[{completion_time:.3f}] OBSERVATION generated ({len(detections)} detections)")

        obs_id = f"OBS-{self.state.total_scans_completed + 1:04d}"
        observation = Observation(
            observation_id=obs_id,
            timestamp=completion_time,
            scan=scan_window,
            detections=detections,
        )

        # Update receiver state
        self.state.status = "IDLE"
        self.state.total_scans_completed += 1
        self.state.total_detections_count += len(detections)
        self.state.last_observation = observation

        # 5. Broadcast RECEIVER_OBSERVATION to EventBus
        await self.event_bus.publish(
            EventMessage(
                type="RECEIVER_OBSERVATION",
                timestamp=completion_time,
                payload=observation.model_dump(),
            )
        )

        return observation
