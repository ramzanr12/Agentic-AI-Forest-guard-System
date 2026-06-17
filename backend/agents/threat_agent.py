"""Threat Agent — fire, poaching, intrusion risk scoring and prediction."""
import asyncio
import random
from datetime import datetime, timezone
from agents.base_agent import BaseAgent
from core.redis_client import set_cache, get_cache
from core.config import settings


class ThreatAgent(BaseAgent):
    def __init__(self):
        super().__init__("ThreatAgent")
        self.scores = {"fire": 25.0, "poaching": 20.0, "intrusion": 15.0}
        self.intrusion_log = []

    async def run(self):
        await self.start()
        while self._running:
            try:
                weather = await get_cache("weather:current") or {}
                detections = await get_cache("vision:latest") or []

                self.scores["fire"] = self._fire_risk(weather, detections)
                self.scores["poaching"] = self._poaching_risk()
                self.scores["intrusion"] = self._intrusion_risk(detections)
                self.scores["animal_movement"] = self._animal_movement()
                self.scores["updated_at"] = datetime.now(timezone.utc).isoformat()

                await set_cache("threat:risk_scores", self.scores, expire=120)
                await self.emit("threats:update", {"scores": self.scores})
                await self._check_thresholds()
                await asyncio.sleep(15)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"ThreatAgent error: {e}")
                await asyncio.sleep(10)

    def _fire_risk(self, weather: dict, detections: list) -> float:
        temp = weather.get("temperature", 28.0)
        humidity = weather.get("humidity", 60.0)
        wind = weather.get("wind_speed", 10.0)
        temp_f = min(100, max(0, (temp - 20) * 3))
        hum_f = max(0, 100 - humidity)
        wind_f = min(100, wind * 3)
        fire_det = sum(15 for d in detections if d.get("class") in ["fire", "smoke"])
        return min(100, max(0, round(
            0.4*temp_f + 0.35*hum_f + 0.15*wind_f + fire_det + random.uniform(-2, 2), 1
        )))

    def _poaching_risk(self) -> float:
        hour = datetime.now(timezone.utc).hour
        night = 70 if (hour >= 20 or hour <= 5) else 15
        weekend = 10 if datetime.now(timezone.utc).weekday() >= 5 else 0
        recent = min(25, len(self.intrusion_log) * 8)
        return min(100, max(0, round(20 + night*0.5 + weekend + recent + random.uniform(-4, 4), 1)))

    def _intrusion_risk(self, detections: list) -> float:
        persons = sum(1 for d in detections if d.get("class") == "person")
        vehicles = sum(1 for d in detections if d.get("class") in ["car","truck","motorcycle"])
        return min(100, max(0, round(10 + persons*15 + vehicles*10 + random.uniform(-3, 3), 1)))

    def _animal_movement(self) -> dict:
        hour = datetime.now(timezone.utc).hour
        if 5 <= hour <= 8 or 17 <= hour <= 20:
            zones = ["Zone-B", "Zone-C", "Water-Source-1"]
        elif hour >= 20 or hour <= 5:
            zones = ["Zone-A", "Zone-D", "Corridor-2"]
        else:
            zones = ["Core-Zone", "Waterhole-Area"]
        return {
            "active_zones": zones,
            "predicted_species": random.sample(["elephant","deer","tiger","leopard"], k=random.randint(1,3)),
            "confidence": round(random.uniform(0.6, 0.85), 2)
        }

    async def _check_thresholds(self):
        if self.scores["fire"] >= settings.fire_risk_threshold:
            await self.emit("alerts:new", {
                "alert_type": "fire_risk",
                "severity": "critical" if self.scores["fire"] >= 85 else "high",
                "description": f"Fire risk at {self.scores['fire']}%. Immediate action required.",
                "lat": 11.4916 + random.uniform(-0.05, 0.05),
                "lon": 76.9294 + random.uniform(-0.05, 0.05),
                "zone": random.choice(["Zone-A","Zone-B","Zone-C"]),
                "confidence": 0.82
            })
        if self.scores["poaching"] >= settings.poaching_risk_threshold:
            await self.emit("alerts:new", {
                "alert_type": "poaching_risk",
                "severity": "high",
                "description": f"Poaching risk elevated to {self.scores['poaching']}%.",
                "lat": 11.4916 + random.uniform(-0.07, 0.07),
                "lon": 76.9294 + random.uniform(-0.07, 0.07),
                "zone": random.choice(["Zone-B","Zone-D"]),
                "confidence": 0.75
            })
