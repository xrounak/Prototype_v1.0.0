"""Unit and integration tests for Environment management and switching."""
import pytest
from httpx import AsyncClient, ASGITransport
from backend.environments.manager import EnvironmentManager
from backend.environments.registry import EnvironmentRegistry
from backend.environments.open_sparse import get_open_sparse_config
from backend.environments.dense_urban import get_dense_urban_config
from backend.environments.mountainous import get_mountainous_config
from backend.environments.frequency_agile import get_frequency_agile_config
from backend.gateway.main import app


def test_environment_registry_and_loading():
    """Verify all 4 standard environments load with valid configs and emitters."""
    registry = EnvironmentRegistry()
    assert "OPEN_SPARSE" in registry.list_environment_ids()
    assert "DENSE_URBAN" in registry.list_environment_ids()
    assert "MOUNTAINOUS" in registry.list_environment_ids()
    assert "FREQUENCY_AGILE" in registry.list_environment_ids()

    open_sparse = get_open_sparse_config()
    assert open_sparse.environment_id == "OPEN_SPARSE"
    assert len(open_sparse.emitters) > 0

    dense_urban = get_dense_urban_config()
    assert dense_urban.environment_id == "DENSE_URBAN"
    assert len(dense_urban.emitters) >= 20

    mountainous = get_mountainous_config()
    assert mountainous.environment_id == "MOUNTAINOUS"
    assert len(mountainous.emitters) >= 8
    # Mountainous should have spatial profile with airborne & ground platforms
    platforms = {em.spatial.platform_type for em in mountainous.emitters if em.spatial}
    assert "GROUND" in platforms
    assert "AIRBORNE" in platforms

    freq_agile = get_frequency_agile_config()
    assert freq_agile.environment_id == "FREQUENCY_AGILE"
    assert len(freq_agile.emitters) >= 10


def test_environment_manager_switching():
    """Verify EnvironmentManager can switch between environments."""
    manager = EnvironmentManager(default_env_id="OPEN_SPARSE")
    assert manager.get_current_environment().environment_id == "OPEN_SPARSE"

    manager.load_environment("DENSE_URBAN")
    assert manager.get_current_environment().environment_id == "DENSE_URBAN"

    manager.load_environment("MOUNTAINOUS")
    assert manager.get_current_environment().environment_id == "MOUNTAINOUS"

    with pytest.raises(ValueError):
        manager.load_environment("INVALID_ENV_NAME")


@pytest.mark.asyncio
async def test_environment_api_endpoints():
    """Verify GET /api/environments, GET /api/environment, and POST /api/environment/select."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. List environments
        res = await client.get("/api/environments")
        assert res.status_code == 200
        envs = res.json()
        env_ids = [e["environment_id"] for e in envs]
        assert "OPEN_SPARSE" in env_ids
        assert "DENSE_URBAN" in env_ids
        assert "MOUNTAINOUS" in env_ids
        assert "FREQUENCY_AGILE" in env_ids

        # 2. Select Mountainous environment
        select_res = await client.post("/api/environment/select", json={"environment_id": "MOUNTAINOUS"})
        assert select_res.status_code == 200
        data = select_res.json()
        assert data["status"] == "ok"
        assert data["environment_id"] == "MOUNTAINOUS"

        # 3. Verify current environment matches
        cur_res = await client.get("/api/environment")
        assert cur_res.status_code == 200
        cur_data = cur_res.json()
        assert cur_data["environment_id"] == "MOUNTAINOUS"

        # 4. Verify system status reflects new environment
        status_res = await client.get("/api/system/status")
        assert status_res.status_code == 200
        status_data = status_res.json()
        assert status_data["environment_id"] == "MOUNTAINOUS"
        assert status_data["total_emitters"] > 0
        assert status_data["simulation_time"] == 0.0  # Reset to 0
