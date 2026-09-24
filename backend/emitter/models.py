"""Data structures for emitter configuration, profiles, and emission events."""
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, model_validator


class EmitterCategory(str, Enum):
    """Broad classification of electromagnetic emitter."""
    RADAR = "RADAR"
    COMMUNICATION = "COMMUNICATION"
    NAVIGATION = "NAVIGATION"
    INTERFERENCE = "INTERFERENCE"
    GENERIC_RADIO_FREQUENCY = "GENERIC_RADIO_FREQUENCY"


class RadarSubtype(str, Enum):
    """Common subtypes for radar emitters."""
    SEARCH = "SEARCH"
    SEARCH_RADAR = "SEARCH_RADAR"
    ACQUISITION = "ACQUISITION"
    ACQUISITION_RADAR = "ACQUISITION_RADAR"
    TRACKING = "TRACKING"
    TRACKING_RADAR = "TRACKING_RADAR"
    AIRBORNE = "AIRBORNE"
    AIRBORNE_RADAR = "AIRBORNE_RADAR"
    CONTINUOUS_WAVE = "CONTINUOUS_WAVE"
    CONTINUOUS_WAVE_RADAR = "CONTINUOUS_WAVE_RADAR"
    EARLY_WARNING = "EARLY_WARNING"
    WEATHER = "WEATHER"


class BehaviorType(str, Enum):
    """Emitter transmission behavior patterns."""
    CONTINUOUS = "CONTINUOUS"
    PERIODIC = "PERIODIC"
    BURST = "BURST"
    JITTERED = "JITTERED"
    STAGGERED = "STAGGERED"
    FREQUENCY_HOPPING = "FREQUENCY_HOPPING"
    FREQUENCY_AGILE = "FREQUENCY_AGILE"


class ModulationType(str, Enum):
    """RF signal modulation types."""
    UNMODULATED = "UNMODULATED"
    LFM = "LFM"
    PHASE_CODED = "PHASE_CODED"
    PHASE_SHIFT_KEYING = "PHASE_SHIFT_KEYING"
    FREQUENCY_SHIFT_KEYING = "FREQUENCY_SHIFT_KEYING"


class RFProfile(BaseModel):
    """Radio frequency specification."""
    center_frequency_hz: float = Field(..., description="RF center frequency in Hertz")
    bandwidth_hz: float = Field(default=10_000_000.0, description="RF bandwidth in Hertz")
    power_dbm: float = Field(default=30.0, description="Transmit power in dBm")


class SpatialProfile(BaseModel):
    """Spatial position and platform representation."""
    x_m: float = 0.0
    y_m: float = 0.0
    z_m: float = 0.0  # Altitude in meters
    platform_type: str = "GROUND"  # GROUND, AIRBORNE, MARITIME


class ModulationProfile(BaseModel):
    """Modulation scheme configuration."""
    type: str = "UNMODULATED"
    parameters: Dict[str, Any] = Field(default_factory=dict)


class BehaviorConfig(BaseModel):
    """Detailed behaviour configuration."""
    type: BehaviorType = BehaviorType.PERIODIC
    pulse_width_us: float = 250.0
    repetition_interval_ms: float = 50.0
    burst_count: int = 3
    burst_interval_ms: float = 500.0
    base_pri_ms: float = 25.0
    jitter_percent: float = 5.0
    pri_sequence_ms: List[float] = Field(default_factory=list)
    hop_frequencies_hz: List[float] = Field(default_factory=list)
    dwell_time_ms: float = 10.0
    min_frequency_hz: float = 0.0
    max_frequency_hz: float = 0.0
    change_interval_ms: float = 25.0


class EmissionEvent(BaseModel):
    """Rich generated RF emission event in the electromagnetic environment."""
    type: str = "EMISSION_EVENT"
    event_id: str
    emitter_id: str
    timestamp: float = Field(..., description="Simulation time (s) when emission starts")
    time_end: float = Field(..., description="Simulation time (s) when emission ends")
    emitter_category: str = "RADAR"
    emitter_subtype: Optional[str] = None
    frequency_start_hz: float
    frequency_end_hz: float
    bandwidth_hz: float
    duration_us: float
    power_dbm: float
    behavior: str
    modulation: str = "UNMODULATED"
    sequence_number: int = 0


class EmitterConfig(BaseModel):
    """Complete composition model of an emitter with backward compatibility."""
    emitter_id: str = Field(..., description="Unique emitter identifier, e.g. E001")
    name: Optional[str] = None
    category: str = "RADAR"
    subtype: Optional[str] = None
    rf: RFProfile
    spatial: Optional[SpatialProfile] = Field(default_factory=SpatialProfile)
    behavior: BehaviorConfig = Field(default_factory=BehaviorConfig)
    modulation: Optional[ModulationProfile] = Field(default_factory=ModulationProfile)
    active: bool = Field(default=True, description="Whether emitter is actively generating")

    @model_validator(mode="before")
    @classmethod
    def normalize_input(cls, data: Any) -> Any:
        """Allow initializing with either flat legacy fields or nested profile fields."""
        if not isinstance(data, dict):
            return data

        d = dict(data)

        # Build rf profile if flat fields are supplied
        if "rf" not in d:
            freq = d.get("frequency_hz", 1_000_000_000.0)
            bw = d.get("bandwidth_hz", 10_000_000.0)
            pwr = d.get("power_dbm", 30.0)
            d["rf"] = RFProfile(center_frequency_hz=freq, bandwidth_hz=bw, power_dbm=pwr)
        elif isinstance(d["rf"], dict):
            d["rf"] = RFProfile(**d["rf"])

        # Build behavior profile if flat fields or legacy fields are supplied
        if "behavior" not in d:
            b_type = d.get("behavior_type", d.get("behavior", BehaviorType.PERIODIC))
            if isinstance(b_type, str):
                try:
                    b_type = BehaviorType(b_type)
                except ValueError:
                    b_type = BehaviorType.PERIODIC
            pulse_w = d.get("pulse_duration_us", d.get("pulse_width_us", 250.0))
            rep_int = d.get("repetition_interval_ms", 50.0)
            b_count = d.get("burst_count", 3)
            d["behavior"] = BehaviorConfig(
                type=b_type,
                pulse_width_us=pulse_w,
                repetition_interval_ms=rep_int,
                burst_count=b_count,
            )
        elif isinstance(d["behavior"], dict):
            # If "pulse" dict is present at top-level (like in x.json), fold it in
            beh_dict = dict(d["behavior"])
            if "pulse" in d and isinstance(d["pulse"], dict):
                pulse = d["pulse"]
                if "width_us" in pulse and "pulse_width_us" not in beh_dict:
                    beh_dict["pulse_width_us"] = pulse["width_us"]
                if "repetition_interval_ms" in pulse and "repetition_interval_ms" not in beh_dict:
                    beh_dict["repetition_interval_ms"] = pulse["repetition_interval_ms"]
            d["behavior"] = BehaviorConfig(**beh_dict)

        # Handle modulation if dict
        if "modulation" in d and isinstance(d["modulation"], dict):
            d["modulation"] = ModulationProfile(**d["modulation"])

        # Handle spatial if dict
        if "spatial" in d and isinstance(d["spatial"], dict):
            d["spatial"] = SpatialProfile(**d["spatial"])

        return d

    # Backward compatibility properties
    @property
    def frequency_hz(self) -> float:
        return self.rf.center_frequency_hz

    @property
    def bandwidth_hz(self) -> float:
        return self.rf.bandwidth_hz

    @property
    def power_dbm(self) -> float:
        return self.rf.power_dbm

    @property
    def pulse_duration_us(self) -> float:
        return self.behavior.pulse_width_us

    @property
    def repetition_interval_ms(self) -> float:
        return self.behavior.repetition_interval_ms

    @property
    def burst_count(self) -> int:
        return self.behavior.burst_count

    @property
    def behavior_type(self) -> BehaviorType:
        return self.behavior.type

    def model_dump(self, *args, **kwargs) -> Dict[str, Any]:
        """Dump model with convenience top-level fields for frontend ease of access."""
        res = super().model_dump(*args, **kwargs)
        # Ensure flat legacy-friendly fields are present in exported dictionary
        res["frequency_hz"] = self.frequency_hz
        res["bandwidth_hz"] = self.bandwidth_hz
        res["power_dbm"] = self.power_dbm
        res["pulse_duration_us"] = self.pulse_duration_us
        res["repetition_interval_ms"] = self.repetition_interval_ms
        res["burst_count"] = self.burst_count
        res["behavior_type"] = self.behavior_type.value
        return res


class EmitterState(BaseModel):
    """Runtime tracking state for an individual emitter."""
    config: EmitterConfig
    total_emissions_count: int = 0
    last_emission_time: Optional[float] = None
    is_active: bool = True
