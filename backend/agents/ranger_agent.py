"""Ranger Agent — tracking, dispatch, patrol routes."""
import asyncio, math, random
from datetime import datetime, timezone
from typing import Dict, List, Optional
from agents.base_agent import BaseAgent
from core.redis_client import set_cache, get_cache


class RangerAgent(BaseAgent):
    def __init__(self):
        super().__init__("RangerAgent")
        self.rangers: Dict[str, dict] = {}
        self._init()

    def _init(self):
        roster = [
            ("R001","Arjun Kumar",  "Zone-A",11.4750,76.9100,True),
            ("R002","Priya Singh",  "Zone-B",11.5200,76.9400,True),
            ("R003","Deepak Rao",   "Zone-C",11.5300,76.9700,False),
            ("R004","Meena Devi",   "Zone-D",11.4600,76.9600,True),
            ("R005","Rajan Pillai", "Core-Zone",11.4916,76.9294,True),
            ("R006","Anitha Nair",  "Zone-A",11.4800,76.9200,False),
            ("R007","Vijay Sharma", "Zone-B",11.5100,76.9500,True),
            ("R008","Lakshmi Iyer", "Zone-C",11.5000,76.9000,True),
        ]
        for badge,name,sector,lat,lon,duty in roster:
            self.rangers[badge] = {
                "id": badge, "badge":badge, "name":name, "sector":sector,
                "lat":lat, "lon":lon, "is_on_duty":duty,
                "status":"patrolling" if duty else "off_duty",
                "phone":f"+91-{random.randint(9000000000,9999999999)}",
                "current_task":None,
                "last_updated":datetime.now(timezone.utc).isoformat()
            }

    async def run(self):
        await self.start()
        while self._running:
            try:
                self._move()
                await set_cache("rangers:live", list(self.rangers.values()), expire=60)
                await self.emit("ranger:status_update",{
                    "rangers": list(self.rangers.values()),
                    "on_duty": sum(1 for r in self.rangers.values() if r["is_on_duty"])
                })
                await asyncio.sleep(8)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"RangerAgent error: {e}")
                await asyncio.sleep(10)

    def _move(self):
        for r in self.rangers.values():
            if not r["is_on_duty"]: continue
            r["lat"] = max(11.40, min(11.60, r["lat"] + random.uniform(-0.002,0.002)))
            r["lon"] = max(76.85, min(77.05, r["lon"] + random.uniform(-0.002,0.002)))
            r["last_updated"] = datetime.now(timezone.utc).isoformat()

    def nearest(self, lat: float, lon: float) -> Optional[dict]:
        cands = [r for r in self.rangers.values()
                 if r["is_on_duty"] and r["status"] != "dispatched"]
        if not cands: return None
        return min(cands, key=lambda r: math.hypot(r["lat"]-lat, r["lon"]-lon))

    async def dispatch(self, alert: dict) -> Optional[dict]:
        r = self.nearest(alert.get("lat",11.4916), alert.get("lon",76.9294))
        if r:
            r["status"] = "dispatched"
            r["current_task"] = alert.get("alert_type","alert")
            await self.emit("ranger:dispatched",{"ranger":r,"alert":alert})
            await set_cache("rangers:live", list(self.rangers.values()), expire=60)
        return r

    def patrol_route(self, sector: str) -> List[dict]:
        base = {
            "Zone-A":(11.47,76.91),"Zone-B":(11.52,76.94),
            "Zone-C":(11.53,76.97),"Zone-D":(11.46,76.96),
            "Core-Zone":(11.49,76.93)
        }.get(sector,(11.4916,76.9294))
        route = []
        for i in range(8):
            a = (i/8)*2*math.pi
            route.append({"lat":base[0]+0.02*math.cos(a),
                          "lon":base[1]+0.02*math.sin(a),"wp":i+1})
        route.append(route[0])
        return route
