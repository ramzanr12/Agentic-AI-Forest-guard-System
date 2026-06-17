"""Volunteer Agent — report handling, points, community feed."""
import asyncio, random
from datetime import datetime, timezone
from agents.base_agent import BaseAgent
from core.redis_client import set_cache, get_cache
from core.database import AsyncSessionLocal
from models.models import Volunteer, VolunteerReport
from sqlalchemy import select, desc


POINTS_MAP = {
    "fire":20, "poaching":25, "animal_sighting":10,
    "trail_damage":8, "illegal_dumping":12, "other":5
}


class VolunteerAgent(BaseAgent):
    def __init__(self):
        super().__init__("VolunteerAgent")

    async def run(self):
        await self.start()
        while self._running:
            try:
                await self._process_pending()
                await self._update_leaderboard()
                await asyncio.sleep(20)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"VolunteerAgent error: {e}")
                await asyncio.sleep(15)

    async def _process_pending(self):
        """Award points for pending approved reports."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(VolunteerReport).where(VolunteerReport.status == "pending")
            )
            reports = result.scalars().all()
            for rep in reports:
                pts = POINTS_MAP.get(rep.incident_type, 5)
                rep.points_awarded = pts
                rep.status = "approved"
                # Update volunteer total
                vol_res = await session.execute(
                    select(Volunteer).where(Volunteer.id == rep.volunteer_id)
                )
                vol = vol_res.scalars().first()
                if vol:
                    vol.points = (vol.points or 0) + pts
                # Escalate critical reports as alerts
                if rep.incident_type in ["fire","poaching"]:
                    await self.emit("alerts:new",{
                        "alert_type": rep.incident_type,
                        "severity": "high",
                        "description": f"Volunteer report: {rep.description[:200]}",
                        "lat": rep.lat, "lon": rep.lon,
                        "source": "volunteer",
                        "confidence": 0.70
                    })
            await session.commit()

    async def _update_leaderboard(self):
        async with AsyncSessionLocal() as session:
            from sqlalchemy.orm import joinedload
            result = await session.execute(
                select(Volunteer).order_by(desc(Volunteer.points)).limit(10)
            )
            vols = result.scalars().all()
            board = []
            for v in vols:
                u_res = await session.execute(
                    select(Volunteer).where(Volunteer.id == v.id)
                )
                board.append({
                    "id": v.id, "points": v.points,
                    "zone": v.zone_assigned, "verified": v.is_verified
                })
            await set_cache("volunteer:leaderboard", board, expire=120)

    async def get_feed(self, limit: int = 20) -> list:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(VolunteerReport).order_by(desc(VolunteerReport.created_at)).limit(limit)
            )
            reports = result.scalars().all()
            return [{
                "id": r.id, "incident_type": r.incident_type,
                "description": r.description[:200], "lat": r.lat, "lon": r.lon,
                "status": r.status, "points": r.points_awarded,
                "created_at": r.created_at.isoformat() if r.created_at else ""
            } for r in reports]
