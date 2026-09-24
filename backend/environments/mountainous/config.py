"""Mountainous environment configuration with spatial elevations and airborne/ground platforms."""
from typing import Optional
from backend.environments.models import EnvironmentConfig, SpectrumLimits
from backend.emitter.models import (
    EmitterConfig,
    RFProfile,
    SpatialProfile,
    BehaviorConfig,
    BehaviorType,
    ModulationProfile,
)

_CACHED_CONFIG: Optional[EnvironmentConfig] = None


def get_mountainous_config() -> EnvironmentConfig:
    """Return Mountainous terrain environment configuration."""
    global _CACHED_CONFIG
    if _CACHED_CONFIG is not None:
        return _CACHED_CONFIG

    emitters = [
        EmitterConfig(
            emitter_id="MNT-01",
            name="Ridge Early Warning Radar",
            category="RADAR",
            subtype="SEARCH",
            rf=RFProfile(center_frequency_hz=1_250_000_000.0, bandwidth_hz=12_000_000.0, power_dbm=45.0),
            spatial=SpatialProfile(x_m=15000.0, y_m=28000.0, z_m=2450.0, platform_type="GROUND"),
            behavior=BehaviorConfig(type=BehaviorType.PERIODIC, pulse_width_us=300.0, repetition_interval_ms=45.0),
            modulation=ModulationProfile(type="LFM"),
        ),
        EmitterConfig(
            emitter_id="MNT-02",
            name="Valley Gap-Filler Radar",
            category="RADAR",
            subtype="ACQUISITION",
            rf=RFProfile(center_frequency_hz=2_800_000_000.0, bandwidth_hz=16_000_000.0, power_dbm=38.0),
            spatial=SpatialProfile(x_m=8000.0, y_m=12000.0, z_m=650.0, platform_type="GROUND"),
            behavior=BehaviorConfig(type=BehaviorType.BURST, pulse_width_us=180.0, repetition_interval_ms=20.0, burst_count=4, burst_interval_ms=400.0),
            modulation=ModulationProfile(type="LFM"),
        ),
        EmitterConfig(
            emitter_id="MNT-03",
            name="Mountain Patrol AEW Radar",
            category="RADAR",
            subtype="AIRBORNE",
            rf=RFProfile(center_frequency_hz=3_300_000_000.0, bandwidth_hz=25_000_000.0, power_dbm=48.0),
            spatial=SpatialProfile(x_m=25000.0, y_m=40000.0, z_m=9200.0, platform_type="AIRBORNE"),
            behavior=BehaviorConfig(type=BehaviorType.JITTERED, pulse_width_us=150.0, base_pri_ms=30.0, jitter_percent=6.0),
            modulation=ModulationProfile(type="LFM"),
        ),
        EmitterConfig(
            emitter_id="MNT-04",
            name="High-Altitude Recon Fighter",
            category="RADAR",
            subtype="TRACKING",
            rf=RFProfile(center_frequency_hz=9_400_000_000.0, bandwidth_hz=35_000_000.0, power_dbm=42.0),
            spatial=SpatialProfile(x_m=18000.0, y_m=22000.0, z_m=5800.0, platform_type="AIRBORNE"),
            behavior=BehaviorConfig(type=BehaviorType.STAGGERED, pulse_width_us=90.0, pri_sequence_ms=[35.0, 50.0, 42.0]),
            modulation=ModulationProfile(type="LFM"),
        ),
        EmitterConfig(
            emitter_id="MNT-05",
            name="Alpine Microwave Relay",
            category="COMMUNICATION",
            subtype="FIXED",
            rf=RFProfile(center_frequency_hz=4_200_000_000.0, bandwidth_hz=20_000_000.0, power_dbm=25.0),
            spatial=SpatialProfile(x_m=12000.0, y_m=31000.0, z_m=2150.0, platform_type="GROUND"),
            behavior=BehaviorConfig(type=BehaviorType.CONTINUOUS),
            modulation=ModulationProfile(type="PHASE_SHIFT_KEYING"),
        ),
        EmitterConfig(
            emitter_id="MNT-06",
            name="Mountain TACAN Beacon",
            category="NAVIGATION",
            subtype="BEACON",
            rf=RFProfile(center_frequency_hz=1_050_000_000.0, bandwidth_hz=4_000_000.0, power_dbm=32.0),
            spatial=SpatialProfile(x_m=14000.0, y_m=19000.0, z_m=1800.0, platform_type="GROUND"),
            behavior=BehaviorConfig(type=BehaviorType.PERIODIC, pulse_width_us=200.0, repetition_interval_ms=15.0),
            modulation=ModulationProfile(type="UNMODULATED"),
        ),
        EmitterConfig(
            emitter_id="MNT-07",
            name="Valley Air Defense Illuminator",
            category="RADAR",
            subtype="TRACKING",
            rf=RFProfile(center_frequency_hz=8_850_000_000.0, bandwidth_hz=20_000_000.0, power_dbm=40.0),
            spatial=SpatialProfile(x_m=6500.0, y_m=16000.0, z_m=780.0, platform_type="GROUND"),
            behavior=BehaviorConfig(type=BehaviorType.JITTERED, pulse_width_us=75.0, base_pri_ms=20.0, jitter_percent=4.0),
            modulation=ModulationProfile(type="LFM"),
        ),
        EmitterConfig(
            emitter_id="MNT-08",
            name="Peak Mountain Jammer",
            category="INTERFERENCE",
            subtype="NOISE_JAMMER",
            rf=RFProfile(center_frequency_hz=1_850_000_000.0, bandwidth_hz=60_000_000.0, power_dbm=46.0),
            spatial=SpatialProfile(x_m=21000.0, y_m=34000.0, z_m=3120.0, platform_type="GROUND"),
            behavior=BehaviorConfig(type=BehaviorType.CONTINUOUS),
            modulation=ModulationProfile(type="FREQUENCY_SHIFT_KEYING"),
        ),
        EmitterConfig(
            emitter_id="MNT-09",
            name="Border Border Surveillance Radar",
            category="RADAR",
            subtype="SEARCH",
            rf=RFProfile(center_frequency_hz=5_600_000_000.0, bandwidth_hz=15_000_000.0, power_dbm=36.0),
            spatial=SpatialProfile(x_m=32000.0, y_m=45000.0, z_m=2850.0, platform_type="GROUND"),
            behavior=BehaviorConfig(type=BehaviorType.PERIODIC, pulse_width_us=220.0, repetition_interval_ms=60.0),
            modulation=ModulationProfile(type="LFM"),
        ),
        EmitterConfig(
            emitter_id="MNT-10",
            name="Surveillance Drone SAR",
            category="RADAR",
            subtype="AIRBORNE",
            rf=RFProfile(center_frequency_hz=14_500_000_000.0, bandwidth_hz=80_000_000.0, power_dbm=34.0),
            spatial=SpatialProfile(x_m=10000.0, y_m=25000.0, z_m=6200.0, platform_type="AIRBORNE"),
            behavior=BehaviorConfig(type=BehaviorType.FREQUENCY_AGILE, pulse_width_us=60.0, min_frequency_hz=14_200_000_000.0, max_frequency_hz=14_800_000_000.0, change_interval_ms=20.0),
            modulation=ModulationProfile(type="LFM"),
        ),
    ]

    _CACHED_CONFIG = EnvironmentConfig(
        environment_id="MOUNTAINOUS",
        name="Mountainous",
        description="Rugged high-relief terrain featuring ground ridge/valley radars and elevated airborne platforms intended for 3D terrain propagation modeling.",
        duration_seconds=60.0,
        spectrum=SpectrumLimits(min_frequency_hz=300_000_000.0, max_frequency_hz=18_000_000_000.0),
        emitter_count=len(emitters),
        emitters=emitters,
    )
    return _CACHED_CONFIG
