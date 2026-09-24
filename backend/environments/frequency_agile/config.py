"""Frequency Agile environment configuration."""
from pathlib import Path
import json
from typing import Optional
from backend.environments.models import EnvironmentConfig, SpectrumLimits
from backend.emitter.models import EmitterConfig

_CACHED_CONFIG: Optional[EnvironmentConfig] = None


def get_frequency_agile_config() -> EnvironmentConfig:
    """Return Frequency Agile environment configuration."""
    global _CACHED_CONFIG
    if _CACHED_CONFIG is not None:
        return _CACHED_CONFIG

    json_path = Path(__file__).resolve().parent.parent.parent / "emitter" / "x.json"
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for env in data.get("environments", []):
                if env.get("id") == "FREQUENCY_AGILE":
                    emitters = [EmitterConfig(**em) for em in env.get("emitters", [])]
                    spec = env.get("spectrum", {})
                    _CACHED_CONFIG = EnvironmentConfig(
                        environment_id="FREQUENCY_AGILE",
                        name=env.get("name", "Frequency Agile"),
                        description=env.get("description", "Dynamic scenario populated by agile radar, hopping waveforms, jittered PRIs, and staggered bursts."),
                        duration_seconds=env.get("duration_seconds", 60.0),
                        spectrum=SpectrumLimits(
                            min_frequency_hz=spec.get("min_frequency_hz", 300_000_000.0),
                            max_frequency_hz=spec.get("max_frequency_hz", 18_000_000_000.0),
                        ),
                        emitter_count=len(emitters),
                        emitters=emitters,
                    )
                    return _CACHED_CONFIG

    raise RuntimeError("Failed to load FREQUENCY_AGILE environment from dataset.")
