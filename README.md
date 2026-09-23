# Modular Electronic Warfare (EW) Radar/Emitter Simulation Suite

A modular, local-first simulation platform for Electronic Warfare (EW) environments, radar/emitter interactions, and high-bandwidth receiver scanning.

Built with **FastAPI (Python 3.10+)**, an async **In-Memory Event Bus**, **Centralized Simulation Clock**, and a modern **Next.js 14 / TypeScript** visualization dashboard.

---

## Architecture Overview

```
                    NEXT.JS FRONTEND (Port 3000)
             [Dashboard | Spectrum Canvas | Event Stream]
                               |
                               | WebSocket & HTTP REST
                               ▼
                    PYTHON GATEWAY (Port 8000)
                 [FastAPI / Lifespan / WS Manager]
                               |
                        [Async Event Bus]
                        /              \
                       ▼                ▼
                EMITTER SERVICE     RECEIVER SERVICE
                [Emitters & Env]   [500MHz Tuner & Detector]
                       \                /
                        \              /
                         ▼            ▼
                      [SIMULATION CLOCK]
```

For complete technical documentation, data flows, and variable lineage, see [docs/CODEBASE_ARCHITECTURE.md](docs/CODEBASE_ARCHITECTURE.md).

---

## Key Features

1. **Decoupled Emitter & Receiver Services**:
   - Emitters generate simulated continuous, periodic, and burst emissions.
   - Receiver operates with a **500 MHz instantaneous bandwidth** constraint.
   - The receiver queries the emitter environment through a clean functional window query (`query_emissions_in_window`), without hard-coded coupling.
2. **Centralized Simulation Clock**:
   - Time is decoupled from wall-clock time. Discrete simulation intervals and scan dwells advance time deterministically.
3. **Live WebSocket Streaming**:
   - Low-latency typed event broadcasts (`EMISSION_EVENT`, `SCAN_REQUEST`, `RECEIVER_OBSERVATION`, `SYSTEM_STATUS`).
4. **Interactive RF Spectrum Visualizer**:
   - 500 MHz to 2.0 GHz dynamic spectrum display showing active emitter bands, instantaneous receiver scan window bracket, and detection hit indicators.
5. **Zero Cloud Dependencies**:
   - Runs 100% locally with virtual environments or Docker Compose.

---

## Quick Start (Local Development)

### Prerequisites
- **Python 3.10+** (tested on 3.11 & 3.13)
- **Node.js 18+** and **npm**

---

### Option A: Running with Local Scripts

#### On Windows:
1. Start the Backend:
   ```cmd
   scripts\run_backend.bat
   ```
2. In a separate terminal, start the Frontend:
   ```cmd
   scripts\run_frontend.bat
   ```
3. Open your browser at `http://localhost:3000`.

#### On Linux / macOS:
1. Make scripts executable and start the Backend:
   ```bash
   chmod +x scripts/*.sh
   ./scripts/run_backend.sh
   ```
2. In a separate terminal, start the Frontend:
   ```bash
   ./scripts/run_frontend.sh
   ```
3. Open `http://localhost:3000`.

---

### Option B: Manual Step-by-Step Commands

#### 1. Setup & Run Backend (FastAPI):
```bash
# From repository root
python -m venv .venv

# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r backend/requirements.txt
uvicorn backend.gateway.main:app --host 0.0.0.0 --port 8000 --reload
```
- Health Check: `http://localhost:8000/health`
- Interactive API Docs: `http://localhost:8000/docs`

#### 2. Setup & Run Frontend (Next.js):
```bash
cd frontend
npm install
npm run dev
```
- Web Application: `http://localhost:3000`

---

### Option C: Running with Docker Compose

Run both the frontend and backend with a single command:
```bash
docker compose up --build
```
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

---

## Testing

Run the automated backend test suite (unit and integration tests):
```bash
# Windows
.\.venv\Scripts\pytest backend\tests

# Linux/macOS
./.venv/bin/pytest backend/tests
```

---

## API Summary

- `GET /health`: Gateway health status.
- `GET /api/system/status`: Global state of all simulation services.
- `POST /api/simulation/start`: Unpause simulation clock.
- `POST /api/simulation/pause`: Pause simulation clock.
- `POST /api/simulation/step`: Step clock by discrete interval (e.g. 25ms).
- `POST /api/simulation/reset`: Reset simulation clock to `0.0s`.
- `GET /api/emitters`: List registered emitters (E001, E002, E003).
- `POST /api/emitter/{id}/toggle`: Toggle emitter active state.
- `POST /api/receiver/scan`: Execute instantaneous bandwidth scan (e.g. 700 to 1200 MHz, 25ms dwell).
- `WebSocket /ws`: Real-time streaming channel for telemetry and event observation.
