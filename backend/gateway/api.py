"""FastAPI API router defining system, emitter, receiver, and simulation endpoints."""
import asyncio
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from backend.shared.models import (
    EmitterConfig,
    ScanRequest,
    Observation,
    SystemStatus,
    EventMessage,
)
from backend.shared.clock import SimulationClock
from backend.shared.events import global_event_bus
from backend.shared.config import settings
from backend.emitter.service import EmitterService
from backend.receiver.service import ReceiverService

router = APIRouter()

# Global state holders initialized by gateway main lifespan
clock = SimulationClock()
emitter_service = EmitterService(event_bus=global_event_bus)
receiver_service = ReceiverService(
    clock=clock,
    emitter_service=emitter_service,
    event_bus=global_event_bus
)

simulation_state = {
    "is_running": False,
    "speed": 1.0,
    "task": None,
}


class StepRequest(BaseModel):
    delta_seconds: float = 0.05  # Default 50ms step


class SimulationControlRequest(BaseModel):
    speed: float = 1.0


# -------------------------------------------------------------
# System & Health
# -------------------------------------------------------------
@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "gateway",
    }


@router.get("/api/system/status", response_model=SystemStatus)
async def get_system_status() -> SystemStatus:
    """Get complete operational status across all services."""
    active_emitters = sum(1 for em in emitter_service.manager.get_all_emitters() if em.active)
    last_obs_id = (
        receiver_service.state.last_observation.observation_id
        if receiver_service.state.last_observation
        else None
    )

    return SystemStatus(
        gateway="CONNECTED",
        emitter_service="RUNNING" if emitter_service.is_running else "STOPPED",
        receiver_service="RUNNING" if receiver_service.is_running else "STOPPED",
        simulation_time=clock.now(),
        simulation_state="RUNNING" if simulation_state["is_running"] else "PAUSED",
        simulation_speed=simulation_state["speed"],
        active_emitters=active_emitters,
        receiver_bandwidth_hz=receiver_service.config.instantaneous_bandwidth_hz,
        last_observation_id=last_obs_id,
    )


# -------------------------------------------------------------
# Emitter Service Endpoints
# -------------------------------------------------------------
@router.post("/api/emitter/start")
async def start_emitter():
    """Start emitter service."""
    emitter_service.start()
    await broadcast_system_status()
    return {"status": "ok", "emitter_service": "RUNNING"}


@router.post("/api/emitter/stop")
async def stop_emitter():
    """Stop emitter service."""
    emitter_service.stop()
    await broadcast_system_status()
    return {"status": "ok", "emitter_service": "STOPPED"}


@router.get("/api/emitters", response_model=List[EmitterConfig])
async def list_emitters():
    """List all registered emitters in the environment."""
    return emitter_service.manager.get_all_emitters()


@router.post("/api/emitters", response_model=EmitterConfig)
async def create_or_update_emitter(emitter: EmitterConfig):
    """Add or update an emitter profile."""
    emitter_service.manager.add_or_update_emitter(emitter)
    await broadcast_system_status()
    return emitter


@router.post("/api/emitter/{emitter_id}/toggle")
async def toggle_emitter(emitter_id: str):
    """Toggle active state of an emitter."""
    em = emitter_service.manager.get_emitter(emitter_id)
    if not em:
        raise HTTPException(status_code=404, detail=f"Emitter {emitter_id} not found")
    new_state = not em.active
    emitter_service.manager.set_active(emitter_id, new_state)
    await broadcast_system_status()
    return {"emitter_id": emitter_id, "active": new_state}


# -------------------------------------------------------------
# Receiver Service Endpoints
# -------------------------------------------------------------
@router.post("/api/receiver/start")
async def start_receiver():
    """Start receiver service."""
    receiver_service.start()
    await broadcast_system_status()
    return {"status": "ok", "receiver_service": "RUNNING"}


@router.post("/api/receiver/stop")
async def stop_receiver():
    """Stop receiver service."""
    receiver_service.stop()
    await broadcast_system_status()
    return {"status": "ok", "receiver_service": "STOPPED"}


@router.get("/api/receiver/state")
async def get_receiver_state():
    """Get current receiver state and configuration."""
    return {
        "config": receiver_service.config.model_dump(),
        "state": receiver_service.state.model_dump(),
    }


@router.post("/api/receiver/scan", response_model=Observation)
async def execute_receiver_scan(request: ScanRequest):
    """Execute an instantaneous bandwidth scan dwell (e.g. 700 MHz -> 1200 MHz, 25ms dwell)."""
    try:
        observation = await receiver_service.execute_scan(request)
        await broadcast_system_status()
        return observation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------------------------------------
# Simulation Engine Endpoints
# -------------------------------------------------------------
@router.post("/api/simulation/start")
async def start_simulation(control: SimulationControlRequest = None):
    """Start running the simulation background clock."""
    simulation_state["is_running"] = True
    if control and control.speed > 0:
        simulation_state["speed"] = control.speed
    await broadcast_system_status()
    return {"status": "ok", "simulation_state": "RUNNING", "speed": simulation_state["speed"]}


@router.post("/api/simulation/pause")
async def pause_simulation():
    """Pause the simulation clock."""
    simulation_state["is_running"] = False
    await broadcast_system_status()
    return {"status": "ok", "simulation_state": "PAUSED"}


@router.post("/api/simulation/reset")
async def reset_simulation():
    """Reset the simulation clock to 0.0s."""
    clock.reset(0.0)
    simulation_state["is_running"] = False
    await broadcast_system_status()
    return {"status": "ok", "simulation_time": 0.0, "simulation_state": "PAUSED"}


@router.post("/api/simulation/step")
async def step_simulation(step_req: StepRequest = StepRequest()):
    """Advance simulation clock by a discrete step and emit events."""
    delta = step_req.delta_seconds
    t_start = clock.now()
    clock.advance(delta)
    t_end = clock.now()

    # Generate emissions during this slice
    emissions = await emitter_service.step_and_publish(t_start, t_end)
    await broadcast_system_status()
    return {
        "time_start": t_start,
        "time_end": t_end,
        "emissions_generated": len(emissions),
    }


async def broadcast_system_status():
    """Publish current system status to EventBus."""
    status = await get_system_status()
    await global_event_bus.publish(
        EventMessage(
            type="SYSTEM_STATUS",
            timestamp=clock.now(),
            payload=status.model_dump(),
        )
    )
