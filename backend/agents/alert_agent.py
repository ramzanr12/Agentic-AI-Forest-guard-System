"""Alert Agent — persists alerts, deduplicates, dispatches rangers."""
import asyncio, random
from datetime import datetime, timezone
from typing import List
from agents.base_agent import BaseAgent
from core.redis_client import set_cache, get_cache
from core.database import AsyncSessionLocal
from models.models import Alert


class AlertAgent(BaseAgent):
    def __init__(self):
        super().__init__("AlertAgent")
        self.buffer: List[dict] = []
        self.recent_ids = set()

    async def run(self):
        await self.start()
        # Seed some alerts for demo
        await self._seed_demo_alerts()
        while self._running:
            try:
                await self._process_buffer()
                await self._refresh_cache()
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"AlertAgent error: {e}")
                await asyncio.sleep(8)

    async def ingest(self, alert: dict):
        """Called by other agents or API to ingest a new alert."""
        key = f"{alert.get('alert_type','')}:{alert.get('zone','')}:{int(alert.get('lat',0)*100)}"
        if key in self.recent_ids:
            return  # deduplicate
        self.recent_ids.add(key)
        if len(self.recent_ids) > 200:
            self.recent_ids = set(list(self.recent_ids)[-100:])
        self.buffer.append(alert)

    async def _process_buffer(self):
        while self.buffer:
            raw = self.buffer.pop(0)
            try:
                async with AsyncSessionLocal() as session:
                    a = Alert(
                        alert_type=raw.get("alert_type","unknown"),
                        severity=raw.get("severity","medium"),
                        lat=raw.get("lat",11.4916),
                        lon=raw.get("lon",76.9294),
                        zone=raw.get("zone","Unknown"),
                        description=raw.get("description",""),
                        confidence=raw.get("confidence",0.8),
                        source=raw.get("source","agent"),
                    )
                    session.add(a)
                    await session.commit()
                    await session.refresh(a)
                    raw["id"] = a.id
                    await self.emit("alert:created", raw)
                    self.logger.info(f"Alert #{a.id} saved: {a.alert_type} [{a.severity}]")
            except Exception as e:
                self.logger.error(f"Alert persist error: {e}")

    async def _refresh_cache(self):
        try:
            async with AsyncSessionLocal() as session:
                from sqlalchemy import select, desc
                result = await session.execute(
                    select(Alert).where(Alert.status=="active")
                    .order_by(desc(Alert.created_at)).limit(50)
                )
                alerts = result.scalars().all()
                data = [{
                    "id":a.id,"alert_type":a.alert_type,"severity":a.severity,
                    "status":a.status,"lat":a.lat,"lon":a.lon,"zone":a.zone,
                    "description":a.description,"confidence":a.confidence,
                    "created_at":a.created_at.isoformat() if a.created_at else ""
                } for a in alerts]
                await set_cache("alerts:active", data, expire=60)
        except Exception as e:
            self.logger.error(f"Alert cache refresh error: {e}")

    async def _seed_demo_alerts(self):
        seeds = [
            ("fire_risk","high",11.480,76.920,"Zone-A","Elevated fire risk in Zone-A"),
            ("poaching","critical",11.510,76.960,"Zone-B","Poacher movement detected"),
            ("intrusion","medium",11.465,76.935,"Zone-D","Unauthorized vehicle entry"),
            ("animal_movement","low",11.500,76.945,"Zone-C","Elephant herd near water source"),
        ]
        for atype,sev,lat,lon,zone,desc in seeds:
            await self.ingest({"alert_type":atype,"severity":sev,"lat":lat,"lon":lon,
                               "zone":zone,"description":desc,"confidence":round(random.uniform(0.7,0.95),2)})
