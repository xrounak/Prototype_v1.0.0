"""Lightweight models and context for receiver scan scheduling."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from backend.shared.models import ScanWindow, Observation


class SchedulerContext(BaseModel):
    """Lightweight context passed to strategies during band selection.
    
    Enables future strategies (e.g. ML, RL) to access simulation history,
    detections, and timing without modifying the receiver interface.
    """
    simulation_time: float = 0.0
    previous_scan: Optional[ScanWindow] = None
    previous_observation: Optional[Observation] = None
    available_bands: List[float] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SchedulerStatus(BaseModel):
    """Status payload representing the active scanner strategy and options."""
    strategy: str
    available_strategies: List[str]


class SetSchedulerStrategyRequest(BaseModel):
    """Request model for setting the active scanner strategy."""
    strategy: str
