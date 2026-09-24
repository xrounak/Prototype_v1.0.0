"""Data models for simulation environments."""
from typing import Any, Dict, List
from pydantic import BaseModel, Field
from backend.emitter.models import EmitterConfig


class SpectrumLimits(BaseModel):
    """Frequency boundaries for an environment's active RF spectrum."""
    min_frequency_hz: float = Field(default=300_000_000.0, description="Minimum frequency (Hz)")
    max_frequency_hz: float = Field(default=18_000_000_000.0, description="Maximum frequency (Hz)")


class EnvironmentSummary(BaseModel):
    """Concise metadata summary of an environment for listing and selection."""
    environment_id: str
    name: str
    description: str
    emitter_count: int
    spectrum: SpectrumLimits


class EnvironmentConfig(BaseModel):
    """Complete specification of an electromagnetic simulation environment."""
    environment_id: str = Field(..., description="Unique environment key, e.g. OPEN_SPARSE")
    name: str = Field(..., description="Human-readable title")
    description: str = Field(..., description="Overview of RF congestion, density, and geography")
    duration_seconds: float = Field(default=60.0, description="Nominal scenario duration")
    spectrum: SpectrumLimits = Field(default_factory=SpectrumLimits)
    emitter_count: int = Field(default=0)
    emitters: List[EmitterConfig] = Field(default_factory=list)
    simulation_settings: Dict[str, Any] = Field(default_factory=dict)

    def to_summary(self) -> EnvironmentSummary:
        """Generate concise summary for API listing."""
        return EnvironmentSummary(
            environment_id=self.environment_id,
            name=self.name,
            description=self.description,
            emitter_count=len(self.emitters),
            spectrum=self.spectrum,
        )
