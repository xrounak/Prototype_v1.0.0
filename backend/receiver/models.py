"""Receiver data models and states."""
from typing import Optional
from pydantic import BaseModel, Field
from backend.shared.models import Observation, ScanWindow


class ReceiverConfig(BaseModel):
    """Receiver hardware & operational parameters."""
    receiver_id: str = "RX-01"
    instantaneous_bandwidth_hz: float = Field(default=500_000_000.0, description="Instantaneous bandwidth (500 MHz)")
    default_dwell_time_ms: float = Field(default=25.0, description="Dwell time in milliseconds")
    min_frequency_hz: float = Field(default=300_000_000.0, description="Minimum tunable frequency (300 MHz)")
    max_frequency_hz: float = Field(default=18_000_000_000.0, description="Maximum tunable frequency (18 GHz)")
    noise_floor_dbm: float = Field(default=-95.0, description="Internal noise floor in dBm")


class ReceiverState(BaseModel):
    """Current runtime state of the receiver."""
    receiver_id: str = "RX-01"
    status: str = "IDLE"  # IDLE, SCANNING, STOPPED
    current_scan_window: Optional[ScanWindow] = None
    total_scans_completed: int = 0
    total_detections_count: int = 0
    last_observation: Optional[Observation] = None
