"""Receiver Service.

Manages receiver hardware state, executes scan commands, queries the emitter
environment via a clean decoupled interface, and generates observations.
Supports both manual tuning dwells and synchronized automated spectrum sweeps.
"""
import logging
import uuid
from typing import Any, List, Optional
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
from backend.scheduler import (
    SchedulerManager,
    SchedulerContext,
    RoundRobinStrategy,
)

logger = logging.getLogger("ew.receiver")


class ReceiverService:
    """Coordinates receiver tuning, environment queries, and observation outputs."""

    def __init__(
        self,
        config: Optional[ReceiverConfig] = None,
        clock: Optional[SimulationClock] = None,
        emitter_service: Optional[EmitterService] = None,
        event_bus: Optional[EventBus] = None,
        scheduler: Optional[SchedulerManager] = None,
        environment_manager: Optional[Any] = None,
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
        self.scheduler: SchedulerManager = scheduler or SchedulerManager()
        self.environment_manager = environment_manager

    @property
    def current_sweep_idx(self) -> int:
        """Deprecated: sweep sequence index is now maintained by the active Scheduler strategy."""
        strategy = self.scheduler.current_strategy
        if isinstance(strategy, RoundRobinStrategy):
            return strategy.index
        return 0

    @current_sweep_idx.setter
    def current_sweep_idx(self, value: int) -> None:
        strategy = self.scheduler.current_strategy
        if isinstance(strategy, RoundRobinStrategy):
            strategy.index = value

    def reset(self) -> None:
        """Reset receiver state and scanner scheduler."""
        self.scheduler.reset()
        self.state.status = "IDLE"
        self.state.current_scan_window = None
        self.state.last_observation = None

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

    def get_sweep_bands(
        self,
        min_freq_hz: Optional[float] = None,
        max_freq_hz: Optional[float] = None,
        step_hz: Optional[float] = None,
    ) -> List[float]:
        """Derive uniform, contiguous sweep frequency bands across the active spectrum.
        
        All parameters can be configured or overridden via function arguments.
        If omitted, boundaries dynamically inherit from the active environment scenario
        or the receiver hardware configuration. No magic frequency numbers are hardcoded.
        
        Args:
            min_freq_hz: Optional minimum frequency override in Hz.
            max_freq_hz: Optional maximum frequency override in Hz.
            step_hz: Optional step size in Hz (defaults to instantaneous bandwidth).
            
        Returns:
            List of starting frequencies in Hz forming a uniform, contiguous spectrum grid.
        """
        start_f = min_freq_hz
        end_f = max_freq_hz

        # Dynamically query active environment's defined spectrum limits if not passed
        if (start_f is None or end_f is None) and self.environment_manager:
            try:
                env = self.environment_manager.get_current_environment()
                if env and hasattr(env, "spectrum") and env.spectrum:
                    if start_f is None:
                        start_f = env.spectrum.min_frequency_hz
                    if end_f is None:
                        end_f = env.spectrum.max_frequency_hz
            except Exception:
                pass

        # Fallback to receiver hardware configuration if still unspecified
        if start_f is None:
            start_f = self.config.min_frequency_hz
        if end_f is None:
            end_f = self.config.max_frequency_hz

        # Clamp within receiver hardware capabilities
        start_f = max(self.config.min_frequency_hz, start_f)
        end_f = min(self.config.max_frequency_hz, end_f)

        step = step_hz if (step_hz and step_hz > 0) else self.config.instantaneous_bandwidth_hz

        # Generate a clean, uniform contiguous frequency grid
        bands: List[float] = []
        curr = start_f
        while curr + step <= end_f + 1.0:
            bands.append(round(curr, 2))
            curr += step

        return bands or [start_f]

    async def step_and_scan(self, time_start_sec: float, time_end_sec: float) -> Optional[Observation]:
        """Execute a synchronized receiver scan dwell during continuous simulation.

        Aligns the dwell window exactly with [time_start_sec, time_end_sec].
        """
        if not self.is_running or not self.auto_scan or time_end_sec <= time_start_sec:
            return None

        bands = self.get_sweep_bands()
        context = SchedulerContext(
            simulation_time=time_start_sec,
            previous_scan=self.state.current_scan_window,
            previous_observation=self.state.last_observation,
            available_bands=bands,
            metadata={"dwell_ms": (time_end_sec - time_start_sec) * 1000.0},
        )
        freq_start = self.scheduler.next_scan(bands=bands, context=context)

        freq_end = freq_start + self.config.instantaneous_bandwidth_hz
        dwell_ms = (time_end_sec - time_start_sec) * 1000.0

        scan_window = ScanWindow(
            action_id=f"SWEEP-{self.state.total_scans_completed + 1}",
            frequency_start_hz=freq_start,
            frequency_end_hz=freq_end,
            dwell_time_ms=round(dwell_ms, 2),
            time_start=round(time_start_sec, 6),
            time_end=round(time_end_sec, 6),
            scheduler_strategy=self.scheduler.get_strategy(),
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
                    "scheduler_strategy": self.scheduler.get_strategy(),
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
        scan_window.scheduler_strategy = self.scheduler.get_strategy()

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
                    "scheduler_strategy": self.scheduler.get_strategy(),
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
