"""Receiver Service.

Manages receiver hardware state, executes scan commands, queries the emitter
environment via a clean decoupled interface, and generates observations.
Supports both manual tuning dwells and synchronized automated spectrum sweeps.
"""
import logging
import uuid
from typing import List, Optional
from backend.shared.models import (
    EventMessage,
    Observation,
    ScanRequest,
    ScanWindow,
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
        self.auto_scan: bool = True  # Automatically sweep spectrum during simulation
        self.current_sweep_idx: int = 0

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

    def get_sweep_bands(self) -> List[float]:
        """Derive sweep frequency tuning bands covering the active environment."""
        bands: List[float] = []

        # If emitter service is available, include bands targeting active emitters
        if self.emitter_service and self.emitter_service.manager:
            active_emitters = [em for em in self.emitter_service.manager.get_all_emitters() if em.active]
            for em in active_emitters:
                center_f = em.rf.center_frequency_hz
                # Center the 500 MHz instantaneous window around emitter if possible
                start_f = max(self.config.min_frequency_hz, center_f - 250_000_000.0)
                end_f = start_f + self.config.instantaneous_bandwidth_hz
                if end_f > self.config.max_frequency_hz:
                    start_f = self.config.max_frequency_hz - self.config.instantaneous_bandwidth_hz
                start_f = round(start_f, -6)
                if start_f not in bands and start_f >= self.config.min_frequency_hz:
                    bands.append(start_f)

        # Baseline sweep bands if none derived or small set
        default_bands = [
            700_000_000.0,
            1_100_000_000.0,
            1_500_000_000.0,
            2_000_000_000.0,
            2_800_000_000.0,
            3_200_000_000.0,
            5_400_000_000.0,
            8_800_000_000.0,
            9_300_000_000.0,
        ]
        for db in default_bands:
            if db not in bands and (db + self.config.instantaneous_bandwidth_hz) <= self.config.max_frequency_hz:
                bands.append(db)

        bands.sort()
        return bands or [700_000_000.0]

    async def step_and_scan(self, time_start_sec: float, time_end_sec: float) -> Optional[Observation]:
        """Execute a synchronized receiver scan dwell during continuous simulation.

        Aligns the dwell window exactly with [time_start_sec, time_end_sec].
        """
        if not self.is_running or not self.auto_scan or time_end_sec <= time_start_sec:
            return None

        bands = self.get_sweep_bands()
        freq_start = bands[self.current_sweep_idx % len(bands)]
        self.current_sweep_idx += 1

        freq_end = freq_start + self.config.instantaneous_bandwidth_hz
        dwell_ms = (time_end_sec - time_start_sec) * 1000.0

        scan_window = ScanWindow(
            action_id=f"SWEEP-{self.state.total_scans_completed + 1}",
            frequency_start_hz=freq_start,
            frequency_end_hz=freq_end,
            dwell_time_ms=round(dwell_ms, 2),
            time_start=round(time_start_sec, 6),
            time_end=round(time_end_sec, 6),
        )

        self.state.status = "SCANNING"
        self.state.current_scan_window = scan_window

        # 1. Publish SCAN_REQUEST to EventBus
        await self.event_bus.publish(
            EventMessage(
                type="SCAN_REQUEST",
                timestamp=scan_window.time_start,
                payload={
                    "action_id": scan_window.action_id,
                    "frequency_start_hz": scan_window.frequency_start_hz,
                    "frequency_end_hz": scan_window.frequency_end_hz,
                    "bandwidth_hz": scan_window.frequency_end_hz - scan_window.frequency_start_hz,
                    "dwell_time_ms": scan_window.dwell_time_ms,
                    "time_start": scan_window.time_start,
                    "time_end": scan_window.time_end,
                },
            )
        )

        # 2. Query emitter environment
        emissions = []
        if self.emitter_service:
            emissions = self.emitter_service.query_emissions_in_window(
                frequency_start_hz=scan_window.frequency_start_hz,
                frequency_end_hz=scan_window.frequency_end_hz,
                time_start_sec=scan_window.time_start,
                time_end_sec=scan_window.time_end,
            )

        # 3. Evaluate detections
        detections = self.detector.evaluate_emissions(
            emissions=emissions,
            scan_window=scan_window,
            noise_floor_dbm=self.config.noise_floor_dbm,
        )

        obs_id = f"OBS-{self.state.total_scans_completed + 1:04d}"
        observation = Observation(
            observation_id=obs_id,
            timestamp=scan_window.time_end,
            scan=scan_window,
            detections=detections,
        )

        self.state.status = "IDLE"
        self.state.total_scans_completed += 1
        self.state.total_detections_count += len(detections)
        self.state.last_observation = observation

        # 4. Broadcast RECEIVER_OBSERVATION
        await self.event_bus.publish(
            EventMessage(
                type="RECEIVER_OBSERVATION",
                timestamp=scan_window.time_end,
                payload=observation.model_dump(),
            )
        )

        return observation

    async def execute_scan(
        self,
        request: ScanRequest,
        advance_clock_if_paused: bool = True
    ) -> Observation:
        """Execute a manual or discrete receiver scan dwell over the requested frequency window."""
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

        # Query emitter environment
        emissions = []
        if self.emitter_service:
            emissions = self.emitter_service.query_emissions_in_window(
                frequency_start_hz=scan_window.frequency_start_hz,
                frequency_end_hz=scan_window.frequency_end_hz,
                time_start_sec=scan_window.time_start,
                time_end_sec=scan_window.time_end,
            )

        # Evaluate detections
        detections = self.detector.evaluate_emissions(
            emissions=emissions,
            scan_window=scan_window,
            noise_floor_dbm=self.config.noise_floor_dbm,
        )

        # Advance simulation clock if clock is attached and advance_clock_if_paused is requested
        if self.clock and advance_clock_if_paused:
            dwell_sec = scan_window.dwell_time_ms / 1000.0
            self.clock.advance(dwell_sec)
            completion_time = self.clock.now()
        else:
            completion_time = scan_window.time_end

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

        # Broadcast RECEIVER_OBSERVATION to EventBus
        await self.event_bus.publish(
            EventMessage(
                type="RECEIVER_OBSERVATION",
                timestamp=completion_time,
                payload=observation.model_dump(),
            )
        )

        return observation
