"""Main FastAPI application for Electronic Warfare Simulation Gateway."""
import asyncio
from contextlib import asynccontextmanager
import logging
from typing import Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.shared.config import settings
from backend.shared.models import EventMessage
from backend.shared.events import global_event_bus
from backend.gateway.websocket import ws_manager
from backend.gateway.api import (
    router as api_router,
    clock,
    emitter_service,
    receiver_service,
    simulation_state,
    get_system_status,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ew.gateway")


# Background simulation runner
async def simulation_loop():
    """Background task advancing clock and generating emitter events when unpaused."""
    logger.info("Simulation background loop started.")
    tick_sec = settings.SIMULATION_TICK_MS / 1000.0

    while True:
        try:
            if simulation_state["is_running"]:
                speed = max(0.1, simulation_state.get("speed", 1.0))
                effective_step = tick_sec * speed

                t_start = clock.now()
                clock.advance(effective_step)
                t_end = clock.now()

                # Step emitters & publish events
                if emitter_service.is_running:
                    await emitter_service.step_and_publish(t_start, t_end)

            await asyncio.sleep(tick_sec)
        except asyncio.CancelledError:
            logger.info("Simulation loop cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in simulation loop: {e}", exc_info=True)
            await asyncio.sleep(1.0)


# EventBus forwarding to WebSocket clients
async def forward_event_to_websocket(event_message: EventMessage):
    """Callback invoked by EventBus to broadcast every event to connected WebSocket clients."""
    await ws_manager.broadcast_event(event_message)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan managing startup and shutdown routines."""
    logger.info("Starting Electronic Warfare Simulation Gateway...")

    # Subscribe WebSocket broadcaster to all EventBus events ('*')
    await global_event_bus.subscribe("*", forward_event_to_websocket)

    # Start simulation background task
    sim_task = asyncio.create_task(simulation_loop())
    simulation_state["task"] = sim_task

    yield

    # Graceful shutdown
    logger.info("Shutting down Gateway...")
    sim_task.cancel()
    try:
        await sim_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Electronic Warfare Simulation Gateway",
    description="FastAPI WebSocket & REST Gateway for modular radar/emitter simulation.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow Next.js dev server on any host/port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register REST endpoints
app.include_router(api_router)


# -------------------------------------------------------------
# WebSocket Endpoint: /ws
# -------------------------------------------------------------
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time event stream WebSocket endpoint.

    Transmits:
    - SYSTEM_STATUS
    - EMISSION_EVENT
    - SCAN_REQUEST
    - RECEIVER_OBSERVATION
    """
    await ws_manager.connect(websocket)

    # Immediately send initial state upon connection
    initial_status = await get_system_status()
    await websocket.send_json({
        "type": "SYSTEM_STATUS",
        "timestamp": clock.now(),
        "payload": initial_status.model_dump(),
    })

    # Also send registered emitters
    emitters = emitter_service.manager.get_all_emitters()
    await websocket.send_json({
        "type": "EMITTER_LIST",
        "timestamp": clock.now(),
        "payload": {"emitters": [em.model_dump() for em in emitters]},
    })

    try:
        while True:
            # Listen for client-side messages (ping or commands)
            data = await websocket.receive_json()
            msg_type = data.get("type", "").upper()

            if msg_type == "PING":
                await websocket.send_json({
                    "type": "PONG",
                    "timestamp": clock.now(),
                    "payload": {"status": "alive"},
                })
            elif msg_type == "SCAN_REQUEST":
                # Handle inline scan request from WebSocket if requested
                from backend.shared.models import ScanRequest
                payload = data.get("payload", {})
                scan_req = ScanRequest(**payload)
                await receiver_service.execute_scan(scan_req)

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.gateway.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=True,
    )
