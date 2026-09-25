"""Unit and integration tests for the receiver scanner/scheduler architecture."""
import pytest
from httpx import AsyncClient, ASGITransport

from backend.scheduler.base import ScanStrategy
from backend.scheduler.models import SchedulerContext
from backend.scheduler.round_robin import RoundRobinStrategy
from backend.scheduler.random import RandomStrategy
from backend.scheduler.manager import SchedulerManager, ScanScheduler
from backend.receiver.service import ReceiverService
from backend.shared.clock import SimulationClock
from backend.shared.events import EventBus
from backend.shared.models import ScanRequest, ScanWindow
from backend.gateway.main import app


# -------------------------------------------------------------
# 1. Round-Robin Strategy Tests
# -------------------------------------------------------------
def test_round_robin_sequential_and_wrap():
    """Verify RoundRobinStrategy returns bands sequentially and wraps cleanly."""
    strategy = RoundRobinStrategy()
    bands = [700_000_000.0, 1_100_000_000.0, 1_500_000_000.0]

    # Test sequential access: B1 -> B2 -> B3 -> B1 -> B2
    assert strategy.select_band(bands) == 700_000_000.0
    assert strategy.select_band(bands) == 1_100_000_000.0
    assert strategy.select_band(bands) == 1_500_000_000.0
    assert strategy.select_band(bands) == 700_000_000.0
    assert strategy.select_band(bands) == 1_100_000_000.0


def test_round_robin_reset():
    """Verify reset returns RoundRobinStrategy to the first band."""
    strategy = RoundRobinStrategy()
    bands = [100.0, 200.0, 300.0]

    assert strategy.select_band(bands) == 100.0
    assert strategy.select_band(bands) == 200.0

    strategy.reset()
    assert strategy.index == 0
    assert strategy.select_band(bands) == 100.0


def test_round_robin_different_band_counts():
    """Verify RoundRobinStrategy handles single band and varying counts."""
    strategy = RoundRobinStrategy()

    # Single band
    single = [500.0]
    assert strategy.select_band(single) == 500.0
    assert strategy.select_band(single) == 500.0

    # Empty bands raises ValueError
    with pytest.raises(ValueError):
        strategy.select_band([])


# -------------------------------------------------------------
# 2. Random Strategy Tests
# -------------------------------------------------------------
def test_random_always_within_available_bands():
    """Verify RandomStrategy always picks a valid window from available bands."""
    strategy = RandomStrategy(seed=42)
    bands = [
        700_000_000.0,
        1_100_000_000.0,
        1_500_000_000.0,
        2_000_000_000.0,
        2_800_000_000.0,
    ]

    for _ in range(50):
        selected = strategy.select_band(bands)
        assert selected in bands


def test_random_single_band():
    """Verify RandomStrategy works with a single available band."""
    strategy = RandomStrategy()
    single = [1_000_000_000.0]
    assert strategy.select_band(single) == 1_000_000_000.0


def test_random_deterministic_seed():
    """Verify seeded RandomStrategy produces deterministic sequences and re-seeds on reset."""
    bands = [10.0, 20.0, 30.0, 40.0, 50.0]
    s1 = RandomStrategy(seed=12345)
    s2 = RandomStrategy(seed=12345)

    seq1 = [s1.select_band(bands) for _ in range(10)]
    seq2 = [s2.select_band(bands) for _ in range(10)]
    assert seq1 == seq2

    # After reset, s1 repeats the same sequence
    s1.reset()
    seq1_reset = [s1.select_band(bands) for _ in range(10)]
    assert seq1_reset == seq1


def test_random_empty_bands_raises():
    """Verify RandomStrategy raises ValueError on empty list."""
    strategy = RandomStrategy()
    with pytest.raises(ValueError):
        strategy.select_band([])


# -------------------------------------------------------------
# 3. Scheduler Manager Tests
# -------------------------------------------------------------
def test_scheduler_manager_defaults_and_switching():
    """Verify SchedulerManager defaults to round_robin and switches properly."""
    manager = SchedulerManager()
    assert manager.get_strategy() == "round_robin"
    assert "round_robin" in manager.get_available_strategies()
    assert "random" in manager.get_available_strategies()

    # Switch to random
    res = manager.set_strategy("random")
    assert res == "random"
    assert manager.get_strategy() == "random"

    # Switch back to round_robin
    res = manager.set_strategy("round_robin")
    assert res == "round_robin"
    assert manager.get_strategy() == "round_robin"


def test_scheduler_manager_unsupported_strategy():
    """Verify attempting to set an unsupported strategy (like 'ml') raises ValueError."""
    manager = SchedulerManager()

    with pytest.raises(ValueError) as excinfo:
        manager.set_strategy("ml")
    assert "Unsupported scan strategy: ml" in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo2:
        manager.set_strategy("reinforcement_learning")
    assert "Unsupported scan strategy: reinforcement_learning" in str(excinfo2.value)


def test_scheduler_manager_reset():
    """Verify manager reset resets all strategies."""
    manager = SchedulerManager()
    bands = [1.0, 2.0, 3.0]
    assert manager.next_scan(bands) == 1.0
    assert manager.next_scan(bands) == 2.0

    manager.reset()
    assert manager.next_scan(bands) == 1.0


def test_scheduler_manager_future_strategy_extensibility():
    """Verify future MLStrategy can be registered without modifying the manager core."""
    class CustomStrategy(ScanStrategy):
        @property
        def name(self) -> str:
            return "custom_prioritized"

        def select_band(self, bands, context=None) -> float:
            return max(bands)

        def reset(self) -> None:
            pass

    manager = SchedulerManager()
    manager.register_strategy("custom_prioritized", CustomStrategy)
    assert "custom_prioritized" in manager.get_available_strategies()

    manager.set_strategy("custom_prioritized")
    assert manager.get_strategy() == "custom_prioritized"
    assert manager.next_scan([100.0, 500.0, 200.0]) == 500.0


# -------------------------------------------------------------
# 4. Receiver Integration Tests
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_receiver_delegates_to_scheduler():
    """Verify ReceiverService asks SchedulerManager for the next band."""
    manager = SchedulerManager(default_strategy="round_robin")
    service = ReceiverService(scheduler=manager)

    # Step receiver and verify band selection
    obs1 = await service.step_and_scan(0.0, 0.025)
    assert obs1 is not None
    assert obs1.scan.scheduler_strategy == "round_robin"

    obs2 = await service.step_and_scan(0.025, 0.050)
    assert obs2 is not None
    # Subsequent scan window moved to next band in sequence
    assert obs2.scan.frequency_start_hz != obs1.scan.frequency_start_hz

    # Switch to random strategy
    service.scheduler.set_strategy("random")
    obs3 = await service.step_and_scan(0.050, 0.075)
    assert obs3 is not None
    assert obs3.scan.scheduler_strategy == "random"
    assert obs3.scan.frequency_start_hz in service.get_sweep_bands()


@pytest.mark.asyncio
async def test_receiver_reset_clears_scheduler():
    """Verify receiver reset resets scheduler index."""
    manager = SchedulerManager(default_strategy="round_robin")
    service = ReceiverService(scheduler=manager)
    bands = service.get_sweep_bands()

    obs1 = await service.step_and_scan(0.0, 0.025)
    assert obs1.scan.frequency_start_hz == bands[0]

    obs2 = await service.step_and_scan(0.025, 0.050)
    assert obs2.scan.frequency_start_hz == bands[1]

    # Reset receiver
    service.reset()
    assert service.current_sweep_idx == 0

    obs3 = await service.step_and_scan(0.050, 0.075)
    assert obs3.scan.frequency_start_hz == bands[0]


# -------------------------------------------------------------
# 5. Gateway REST API Scheduler Tests
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_api_get_scheduler():
    """Verify GET /api/receiver/scheduler returns active strategy and available list."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/receiver/scheduler")
        assert response.status_code == 200
        data = response.json()
        assert "strategy" in data
        assert "available_strategies" in data
        assert "round_robin" in data["available_strategies"]
        assert "random" in data["available_strategies"]


@pytest.mark.asyncio
async def test_api_set_scheduler_success_and_validation():
    """Verify POST /api/receiver/scheduler sets strategy and rejects unsupported ones."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Set to random
        res = await client.post("/api/receiver/scheduler", json={"strategy": "random"})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["strategy"] == "random"

        # Check system status exposes scanner_strategy
        status_res = await client.get("/api/system/status")
        assert status_res.status_code == 200
        status_data = status_res.json()
        assert status_data["scanner_strategy"] == "random"

        # Reject unsupported "ml"
        err_res = await client.post("/api/receiver/scheduler", json={"strategy": "ml"})
        assert err_res.status_code == 400
        err_data = err_res.json()
        assert err_data["detail"] == "Unsupported scan strategy: ml"

        # Set back to round_robin
        res2 = await client.post("/api/receiver/scheduler", json={"strategy": "round_robin"})
        assert res2.status_code == 200
        assert res2.json()["strategy"] == "round_robin"
