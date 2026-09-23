"""API endpoint tests for Gateway."""
import pytest
from httpx import AsyncClient, ASGITransport
from backend.gateway.main import app


@pytest.mark.asyncio
async def test_health_check():
    """Verify GET /health returns ok."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "gateway"


@pytest.mark.asyncio
async def test_system_status():
    """Verify GET /api/system/status returns correct components."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/system/status")
        assert response.status_code == 200
        data = response.json()
        assert data["gateway"] == "CONNECTED"
        assert data["emitter_service"] in ["RUNNING", "STOPPED"]
        assert data["receiver_service"] in ["RUNNING", "STOPPED"]
        assert data["receiver_bandwidth_hz"] == 500_000_000.0


@pytest.mark.asyncio
async def test_receiver_scan_endpoint():
    """Verify POST /api/receiver/scan produces valid observation."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "action_id": 999,
            "frequency_start_hz": 700_000_000.0,
            "bandwidth_hz": 500_000_000.0,
            "dwell_time_ms": 25.0,
        }
        response = await client.post("/api/receiver/scan", json=payload)
        assert response.status_code == 200
        obs = response.json()
        assert obs["type"] == "RECEIVER_OBSERVATION"
        assert obs["scan"]["frequency_start_hz"] == 700_000_000.0
        assert obs["scan"]["frequency_end_hz"] == 1_200_000_000.0
        assert "detections" in obs
