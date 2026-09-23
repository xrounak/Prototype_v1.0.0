"""Data structures for emitter configuration and state."""
from typing import Optional
from pydantic import BaseModel, Field
from backend.shared.models import BehaviorType, EmitterConfig


class EmitterState(BaseModel):
    """Runtime tracking state for an individual emitter."""
    config: EmitterConfig
    total_emissions_count: int = 0
    last_emission_time: Optional[float] = None
    is_active: bool = True
