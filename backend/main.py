"""
Forest Guard — FastAPI main application entry point.
Starts all agents as background asyncio tasks.
"""
import asyncio
import logging
import sys
import os

sys.path.insert(0, "/app")

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from core.database import init_db
from core.redis_client import get_cache, set_cache
from core.config import settings

# API Routers
from api.auth       import router as auth_router
from api.alerts     import router as alerts_router
from api.rangers    import router as rangers_router
from api.visitors   import router as visitors_router
from api.volunteers import router as volunteers_router
from api.wildlife   import router as wildlife_router
from api.dashboard  import router as dashboard_router
from api.reports    import router as reports_router
from api.ai_chat    import router as ai_router
from api.routing    import router as routing_router

# Agents
from agents.planner_agent   import PlannerAgent
from agents.vision_agent    import VisionAgent
from agents.threat_agent    import ThreatAgent
from agents.wildlife_agent  import WildlifeAgent
from agents.geospatial_agent import GeospatialAgent
from agents.ranger_agent    import RangerAgent
from agents.alert_agent     import AlertAgent
from agents.visitor_agent   import VisitorAgent
from agents.volunteer_agent import VolunteerAgent
from agents.report_agent    import ReportAgent
from agents.logger_agent    import LoggerAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("main")

# Global agent instances
_agents = {}
_tasks  = []

# WebSocket connection manager
class WSManager:
    def __init__(self):
        self.connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)

    def disconnect(self, ws: WebSocket):
        self.connections.discard(ws) if hasattr(self.connections,'discard') else None
        if ws in self.connections:
            self.connections.remove(ws)

    async def broadcast(self, data: dict):
        dead = []
        for ws in self.connections:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

ws_manager = WSManager()


async def _run_agent(agent):
    """Run agent with fault tolerance — restart on crash."""
    while True:
        try:
            await agent.run()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Agent {agent.name} crashed: {e}. Restarting in 10s...")
            await asyncio.sleep(10)


async def _ws_broadcaster():
    """Periodically push state to all WebSocket clients."""
    while True:
        try:
            state   = await get_cache("system:state") or {}
            alerts  = await get_cache("alerts:active") or []
            rangers = await get_cache("rangers:live") or []
            scores  = await get_cache("threat:risk_scores") or {}
            payload = {
                "type":       "state_update",
                "timestamp":  datetime.now(timezone.utc).isoformat(),
                "state":      state,
                "alerts":     alerts[:10],
                "rangers":    rangers,
                "risk_scores":scores,
            }
            await ws_manager.broadcast(payload)
        except Exception as e:
            logger.error(f"WS broadcast error: {e}")
        await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────
    logger.info("=" * 55)
    logger.info("  Agentic AI Forest Guard — Starting Up")
    logger.info("=" * 55)

    await init_db()
    logger.info("Database ready.")

    # Instantiate agents
    _agents["planner"]    = PlannerAgent()
    _agents["vision"]     = VisionAgent()
    _agents["threat"]     = ThreatAgent()
    _agents["wildlife"]   = WildlifeAgent()
    _agents["geospatial"] = GeospatialAgent()
    _agents["ranger"]     = RangerAgent()
    _agents["alert"]      = AlertAgent()
    _agents["visitor"]    = VisitorAgent()
    _agents["volunteer"]  = VolunteerAgent()
    _agents["report"]     = ReportAgent()
    _agents["logger"]     = LoggerAgent()

    # Start all agents as background tasks
    for name, agent in _agents.items():
        t = asyncio.create_task(_run_agent(agent), name=f"agent-{name}")
        _tasks.append(t)
        logger.info(f"  ✓ {name} agent started")

    # Start WebSocket broadcaster
    _tasks.append(asyncio.create_task(_ws_broadcaster(), name="ws-broadcaster"))

    logger.info(f"All {len(_agents)} agents running.")
    logger.info(f"API ready at http://0.0.0.0:{8000}")
    logger.info("=" * 55)

    yield

    # ── Shutdown ─────────────────────────────────────────────
    logger.info("Shutting down agents...")
    for t in _tasks:
        t.cancel()
    await asyncio.gather(*_tasks, return_exceptions=True)
    logger.info("Forest Guard shut down cleanly.")


# ── FastAPI App ───────────────────────────────────────────────────────────
app = FastAPI(
    title="Agentic AI Forest Guard",
    description="Smart Forest Intelligence System — Multi-Agent Platform",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
os.makedirs("/app/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="/app/static"), name="static")

# Register routers
for router in [
    auth_router, alerts_router, rangers_router, visitors_router,
    volunteers_router, wildlife_router, dashboard_router,
    reports_router, ai_router, routing_router,
]:
    app.include_router(router)


# ── Core Endpoints ────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "Forest Guard Backend",
        "version": "2.0.0",
        "agents": list(_agents.keys()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/")
async def root():
    return {
        "message": f"🌿 {settings.forest_name} — Intelligence API",
        "docs": "/docs",
        "health": "/health",
        "version": "2.0.0",
    }


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws_manager.connect(ws)
    logger.info(f"WebSocket client connected. Total: {len(ws_manager.connections)}")
    try:
        while True:
            data = await ws.receive_text()
            # Echo back for ping/pong
            await ws.send_json({"type": "pong", "received": data})
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
        logger.info("WebSocket client disconnected.")
