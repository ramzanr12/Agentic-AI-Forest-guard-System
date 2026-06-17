"""Planner Agent — central orchestrator, task dispatcher."""
import asyncio
import random
from datetime import datetime, timezone
from agents.base_agent import BaseAgent
from core.redis_client import set_cache, get_cache


class PlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__("PlannerAgent")
        self.state = {}

    async def on_start(self):
        self.state = {
            "active_alerts": random.randint(1, 5),
            "rangers_on_duty": random.randint(4, 8),
            "visitors_inside": random.randint(15, 60),
            "fire_risk": random.randint(15, 45),
            "poaching_risk": random.randint(10, 35),
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        await set_cache("system:state", self.state, expire=120)

    async def run(self):
        await self.start()
        while self._running:
            try:
                # Update system state
                scores = await get_cache("threat:risk_scores") or {}
                rangers = await get_cache("rangers:live") or []
                on_duty = sum(1 for r in rangers if r.get("is_on_duty", False))

                self.state.update({
                    "fire_risk": scores.get("fire", self.state.get("fire_risk", 25)),
                    "poaching_risk": scores.get("poaching", self.state.get("poaching_risk", 20)),
                    "rangers_on_duty": on_duty or self.state.get("rangers_on_duty", 5),
                    "last_updated": datetime.now(timezone.utc).isoformat()
                })
                await set_cache("system:state", self.state, expire=120)
                await self.emit("system:state_update", {"state": self.state})
                await asyncio.sleep(12)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"PlannerAgent error: {e}")
                await asyncio.sleep(10)
