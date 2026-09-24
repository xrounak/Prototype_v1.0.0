"""Shared Pydantic models for the Electronic Warfare simulation."""
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator

# Re-export key emitter models for convenience
from backend.emitter.models import (
    BehaviorType,
    EmitterConfig,
    EmissionEvent,
)


class ScanRequest(BaseModel):
    """Scan / tune request dispatched to the receiver."""
    type: str = "SCAN_REQUEST"
    action_id: str | int = 1001
    frequency_start_hz: float = Field(..., description="Tuning start frequency in Hz")
    bandwidth_hz: Optional[float] = Field(default=500_000_000.0, description="Receiver instantaneous bandwidth in Hz")
    dwell_time_ms: Optional[float] = Field(default=25.0, description="Tuning dwell duration in milliseconds")
    state_version: int = 1


class ScanWindow(BaseModel):
    """The evaluated scan window."""
    action_id: Optional[str | int] = None
    frequency_start_hz: float
    frequency_end_hz: float
    dwell_time_ms: float
    time_start: float
    time_end: float


class Detection(BaseModel):
    """A detected emission within the receiver's scan window preserving emitter metadata."""
    detection_id: str
    emitter_id: str
    emitter_category: str = "RADAR"
    emitter_subtype: Optional[str] = None
    frequency_start_hz: float
    frequency_end_hz: float
    detected_power_dbm: float
    timestamp: float
    duration_us: float
    overlap_ratio: float = 1.0
    behaviour: str = "PERIODIC"
    modulation: str = "UNMODULATED"

    @property
    def observed_power_dbm(self) -> float:
        return self.detected_power_dbm

    def model_dump(self, *args, **kwargs) -> Dict[str, Any]:
        d = super().model_dump(*args, **kwargs)
        d["observed_power_dbm"] = self.detected_power_dbm
        return d


class Observation(BaseModel):
    """Receiver observation returned after completing a scan dwell."""
    type: str = "RECEIVER_OBSERVATION"
    observation_id: str
    timestamp: float = Field(..., description="Simulation time at completion of dwell")
    scan: ScanWindow
    detections: List[Detection] = Field(default_factory=list)


class SystemStatus(BaseModel):
    """Overall status of the EW simulation system."""
    gateway: str = "CONNECTED"
    emitter_service: str = "RUNNING"
    receiver_service: str = "RUNNING"
    simulation_time: float = 0.0
    simulation_state: str = "PAUSED"  # RUNNING | PAUSED | STOPPED
    simulation_speed: float = 1.0
    environment_id: str = "OPEN_SPARSE"
    environment_name: str = "Open Sparse"
    total_emitters: int = 0
    active_emitters: int = 0
    receiver_bandwidth_hz: float = 500_000_000.0
    last_observation_id: Optional[str] = None


class EventMessage(BaseModel):
    """Standard message envelope broadcast over EventBus and WebSocket."""
    type: str
    timestamp: float
    payload: Dict[str, Any]
