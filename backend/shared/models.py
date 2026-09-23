"""Shared Pydantic models for the Electronic Warfare simulation."""
from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class BehaviorType(str, Enum):
    """Emitter behavior patterns."""
    CONTINUOUS = "CONTINUOUS"
    PERIODIC = "PERIODIC"
    BURST = "BURST"


class EmitterConfig(BaseModel):
    """Specification of a radar or emitter source."""
    emitter_id: str = Field(..., description="Unique emitter identifier, e.g. E001")
    name: Optional[str] = None
    frequency_hz: float = Field(..., description="Center frequency in Hertz")
    bandwidth_hz: float = Field(default=10_000_000.0, description="Signal bandwidth in Hertz")
    power_dbm: float = Field(default=30.0, description="Transmit power in dBm")
    pulse_duration_us: float = Field(default=250.0, description="Pulse width in microseconds")
    repetition_interval_ms: float = Field(default=50.0, description="Pulse repetition interval in ms")
    burst_count: int = Field(default=3, description="Pulses per burst for BURST mode")
    behavior_type: BehaviorType = Field(default=BehaviorType.BURST)
    active: bool = Field(default=True, description="Whether emitter is actively generating")


class EmissionEvent(BaseModel):
    """Generated RF emission event in the electromagnetic environment."""
    type: str = "EMISSION_EVENT"
    event_id: str
    emitter_id: str
    timestamp: float = Field(..., description="Simulation time (s) when emission starts")
    time_end: float = Field(..., description="Simulation time (s) when emission ends")
    frequency_start_hz: float
    frequency_end_hz: float
    duration_us: float
    power_dbm: float
    behavior: str


class ScanRequest(BaseModel):
    """Scan / tune request dispatched to the receiver."""
    type: str = "SCAN_REQUEST"
    action_id: str | int = 1001
    frequency_start_hz: float = Field(..., description="Tuning start frequency in Hz")
    bandwidth_hz: float = Field(default=500_000_000.0, description="Receiver instantaneous bandwidth in Hz")
    dwell_time_ms: float = Field(default=25.0, description="Tuning dwell duration in milliseconds")
    state_version: int = 1


class ScanWindow(BaseModel):
    """The evaluated scan window."""
    frequency_start_hz: float
    frequency_end_hz: float
    dwell_time_ms: float
    time_start: float
    time_end: float


class Detection(BaseModel):
    """A detected emission within the receiver's scan window."""
    detection_id: str
    emitter_id: str
    frequency_start_hz: float
    frequency_end_hz: float
    detected_power_dbm: float
    timestamp: float
    duration_us: float
    overlap_ratio: float = 1.0


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
    active_emitters: int = 0
    receiver_bandwidth_hz: float = 500_000_000.0
    last_observation_id: Optional[str] = None


class EventMessage(BaseModel):
    """Standard message envelope broadcast over WebSocket."""
    type: str
    timestamp: float
    payload: dict[str, Any]
