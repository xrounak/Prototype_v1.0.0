"""Unit tests for emitter behaviour strategies and rich emission event generation."""
import pytest
from backend.emitter.models import (
    EmitterConfig,
    RFProfile,
    BehaviorConfig,
    BehaviorType,
    ModulationProfile,
)
from backend.emitter.generator import EmissionEventGenerator
from backend.emitter.behaviours import (
    ContinuousBehaviour,
    PeriodicBehaviour,
    BurstBehaviour,
    JitteredBehaviour,
    StaggeredBehaviour,
    FrequencyHoppingBehaviour,
    FrequencyAgileBehaviour,
)


def test_continuous_behaviour():
    """Verify ContinuousBehaviour produces single span emission with matching duration."""
    emitter = EmitterConfig(
        emitter_id="EM-CONT",
        rf=RFProfile(center_frequency_hz=1e9, bandwidth_hz=20e6, power_dbm=28.0),
        behavior=BehaviorConfig(type=BehaviorType.CONTINUOUS),
    )
    events = EmissionEventGenerator.generate_events_for_emitter(emitter, 0.0, 0.1)
    assert len(events) == 1
    ev = events[0]
    assert ev.behavior == "CONTINUOUS"
    assert ev.timestamp == 0.0
    assert ev.time_end == 0.1
    assert ev.frequency_start_hz == 1e9 - 10e6
    assert ev.frequency_end_hz == 1e9 + 10e6


def test_periodic_behaviour():
    """Verify PeriodicBehaviour generates pulses at regular intervals."""
    emitter = EmitterConfig(
        emitter_id="EM-PER",
        rf=RFProfile(center_frequency_hz=2e9, bandwidth_hz=10e6, power_dbm=35.0),
        behavior=BehaviorConfig(type=BehaviorType.PERIODIC, pulse_width_us=100.0, repetition_interval_ms=20.0),
    )
    # 0 to 100ms should contain 5 pulses (at 0, 20, 40, 60, 80, 100ms)
    events = EmissionEventGenerator.generate_events_for_emitter(emitter, 0.0, 0.1)
    assert len(events) >= 5
    for ev in events:
        assert ev.behavior == "PERIODIC"
        assert ev.duration_us == 100.0


def test_burst_behaviour():
    """Verify BurstBehaviour generates groups of pulses."""
    emitter = EmitterConfig(
        emitter_id="EM-BURST",
        rf=RFProfile(center_frequency_hz=3e9, bandwidth_hz=15e6, power_dbm=30.0),
        behavior=BehaviorConfig(
            type=BehaviorType.BURST,
            pulse_width_us=50.0,
            repetition_interval_ms=10.0,
            burst_count=3,
            burst_interval_ms=200.0,
        ),
    )
    # Over 0.5s, expect bursts at 0ms and 200ms and 400ms, each with 3 pulses = 9 pulses
    events = EmissionEventGenerator.generate_events_for_emitter(emitter, 0.0, 0.5)
    assert len(events) == 9
    assert all(ev.behavior == "BURST" for ev in events)


def test_jittered_behaviour():
    """Verify JitteredBehaviour introduces deterministic PRI variance."""
    emitter = EmitterConfig(
        emitter_id="EM-JIT",
        rf=RFProfile(center_frequency_hz=4e9, bandwidth_hz=10e6, power_dbm=32.0),
        behavior=BehaviorConfig(
            type=BehaviorType.JITTERED,
            pulse_width_us=80.0,
            base_pri_ms=25.0,
            jitter_percent=8.0,
        ),
    )
    events = EmissionEventGenerator.generate_events_for_emitter(emitter, 0.0, 0.2)
    assert len(events) >= 7
    # Verify pulse start times vary slightly from pure regular multiples
    starts = [ev.timestamp for ev in events]
    differences = [starts[i+1] - starts[i] for i in range(len(starts)-1)]
    # At least two interval differences must differ due to jitter
    assert len(set(round(d, 5) for d in differences)) > 1


def test_staggered_behaviour():
    """Verify StaggeredBehaviour cycles through the defined PRI sequence."""
    emitter = EmitterConfig(
        emitter_id="EM-STAG",
        rf=RFProfile(center_frequency_hz=5e9, bandwidth_hz=12e6, power_dbm=30.0),
        behavior=BehaviorConfig(
            type=BehaviorType.STAGGERED,
            pulse_width_us=60.0,
            pri_sequence_ms=[20.0, 40.0, 30.0],
        ),
    )
    # Cycle duration = 20 + 40 + 30 = 90ms.
    # In 200ms, expect 2 full cycles (6 pulses) + part of 3rd cycle = 7 pulses
    events = EmissionEventGenerator.generate_events_for_emitter(emitter, 0.0, 0.2)
    assert len(events) >= 6
    intervals = [round((events[i+1].timestamp - events[i].timestamp) * 1000, 1) for i in range(len(events)-1)]
    assert 20.0 in intervals
    assert 40.0 in intervals
    assert 30.0 in intervals


def test_frequency_hopping_behaviour():
    """Verify FrequencyHoppingBehaviour shifts center frequencies across hops."""
    hops = [9.2e9, 9.4e9, 9.6e9, 9.8e9]
    emitter = EmitterConfig(
        emitter_id="EM-HOP",
        rf=RFProfile(center_frequency_hz=9.5e9, bandwidth_hz=20e6, power_dbm=40.0),
        behavior=BehaviorConfig(
            type=BehaviorType.FREQUENCY_HOPPING,
            pulse_width_us=100.0,
            repetition_interval_ms=10.0,
            hop_frequencies_hz=hops,
            dwell_time_ms=20.0,
        ),
    )
    events = EmissionEventGenerator.generate_events_for_emitter(emitter, 0.0, 0.1)
    assert len(events) >= 8
    # Center frequencies of generated events should match items from hops list
    observed_centers = {round((ev.frequency_start_hz + ev.frequency_end_hz) / 2.0, -6) for ev in events}
    for c in observed_centers:
        assert any(abs(c - h) < 1e6 for h in hops)


def test_frequency_agile_behaviour():
    """Verify FrequencyAgileBehaviour bounds emissions within min and max frequencies."""
    min_f = 8.5e9
    max_f = 9.0e9
    emitter = EmitterConfig(
        emitter_id="EM-AGILE",
        rf=RFProfile(center_frequency_hz=8.75e9, bandwidth_hz=15e6, power_dbm=36.0),
        behavior=BehaviorConfig(
            type=BehaviorType.FREQUENCY_AGILE,
            pulse_width_us=50.0,
            repetition_interval_ms=15.0,
            min_frequency_hz=min_f,
            max_frequency_hz=max_f,
            change_interval_ms=20.0,
        ),
    )
    events = EmissionEventGenerator.generate_events_for_emitter(emitter, 0.0, 0.2)
    assert len(events) >= 10
    for ev in events:
        assert ev.behavior == "FREQUENCY_AGILE"
        center_f = (ev.frequency_start_hz + ev.frequency_end_hz) / 2.0
        assert min_f <= center_f <= max_f
