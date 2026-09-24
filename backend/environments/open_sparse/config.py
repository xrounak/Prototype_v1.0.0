"""Open Sparse environment configuration."""
from pathlib import Path
import json
from typing import Optional
from backend.environments.models import EnvironmentConfig, SpectrumLimits
from backend.emitter.models import EmitterConfig

_CACHED_CONFIG: Optional[EnvironmentConfig] = None


def get_open_sparse_config() -> EnvironmentConfig:
    """Return Open Sparse environment configuration."""
    global _CACHED_CONFIG
    if _CACHED_CONFIG is not None:
        return _CACHED_CONFIG

    json_path = Path(__file__).resolve().parent.parent.parent / "emitter" / "x.json"
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for env in data.get("environments", []):
                if env.get("id") == "OPEN_SPARSE":
                    emitters = [EmitterConfig(**em) for em in env.get("emitters", [])]
                    spec = env.get("spectrum", {})
                    _CACHED_CONFIG = EnvironmentConfig(
                        environment_id="OPEN_SPARSE",
                        name=env.get("name", "Open Sparse"),
                        description=env.get("description", "Low-density electromagnetic environment with clearly separated synthetic emitters."),
                        duration_seconds=env.get("duration_seconds", 60.0),
                        spectrum=SpectrumLimits(
                            min_frequency_hz=spec.get("min_frequency_hz", 300_000_000.0),
                            max_frequency_hz=spec.get("max_frequency_hz", 18_000_000_000.0),
                        ),
                        emitter_count=len(emitters),
                        emitters=emitters,
                    )
                    return _CACHED_CONFIG

    # Fallback definition if x.json is not present
    from backend.emitter.models import RFProfile, BehaviorConfig, BehaviorType
    fallback_emitters = [
        EmitterConfig(
            emitter_id="E001",
            name="Search Radar 01",
            category="RADAR",
            subtype="SEARCH",
            rf=RFProfile(center_frequency_hz=1_300_000_000.0, bandwidth_hz=10_000_000.0, power_dbm=30.0),
            behavior=BehaviorConfig(type=BehaviorType.PERIODIC, pulse_width_us=250.0, repetition_interval_ms=50.0),
        ),
        EmitterConfig(
            emitter_id="E002",
            name="Tracking Radar 01",
            category="RADAR",
            subtype="TRACKING",
            rf=RFProfile(center_frequency_hz=3_100_000_000.0, bandwidth_hz=20_000_000.0, power_dbm=35.0),
            behavior=BehaviorConfig(type=BehaviorType.PERIODIC, pulse_width_us=100.0, repetition_interval_ms=40.0),
        ),
        EmitterConfig(
            emitter_id="E003",
            name="Airborne Radar 01",
            category="RADAR",
            subtype="AIRBORNE",
            rf=RFProfile(center_frequency_hz=9_200_000_000.0, bandwidth_hz=30_000_000.0, power_dbm=38.0),
            behavior=BehaviorConfig(type=BehaviorType.JITTERED, pulse_width_us=120.0, base_pri_ms=25.0, jitter_percent=5.0),
        ),
    ]
    _CACHED_CONFIG = EnvironmentConfig(
        environment_id="OPEN_SPARSE",
        name="Open Sparse",
        description="Low-density baseline environment with separated emitters.",
        duration_seconds=60.0,
        spectrum=SpectrumLimits(min_frequency_hz=300_000_000.0, max_frequency_hz=18_000_000_000.0),
        emitter_count=len(fallback_emitters),
        emitters=fallback_emitters,
    )
    return _CACHED_CONFIG
