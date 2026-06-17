"""Wildlife Agent — animal ID tracking, population stats, sighting history."""
import asyncio
import random
import uuid
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import Dict, List
from agents.base_agent import BaseAgent
from core.redis_client import set_cache, get_cache


POPULATION = {
    "elephant": {"count": 47, "trend": "stable",     "icon": "🐘"},
    "tiger":    {"count": 12, "trend": "increasing",  "icon": "🐯"},
    "deer":     {"count": 230,"trend": "stable",      "icon": "🦌"},
    "leopard":  {"count": 8,  "trend": "stable",      "icon": "🐆"},
    "bear":     {"count": 15, "trend": "decreasing",  "icon": "🐻"},
    "peacock":  {"count": 89, "trend": "increasing",  "icon": "🦚"},
    "crocodile":{"count": 23, "trend": "stable",      "icon": "🐊"},
}


class WildlifeAgent(BaseAgent):
    def __init__(self):
        super().__init__("WildlifeAgent")
        self.registry: Dict[str, dict] = {}
        self.sightings: List[dict] = []
        self.counts: Dict[str, int] = defaultdict(int)
        self._seed_registry()

    def _seed_registry(self):
        for species, count in [("elephant",6),("tiger",3),("deer",10),("leopard",2),("bear",3)]:
            for _ in range(count):
                aid = f"{species[:3].upper()}-{uuid.uuid4().hex[:6].upper()}"
                self.registry[aid] = {
                    "id": aid, "species": species,
                    "first_seen": (datetime.now(timezone.utc) - timedelta(days=random.randint(1,180))).isoformat(),
                    "last_seen": datetime.now(timezone.utc).isoformat(),
                    "last_lat": 11.4916 + random.uniform(-0.1, 0.1),
                    "last_lon": 76.9294 + random.uniform(-0.1, 0.1),
                    "sighting_count": random.randint(1, 40),
                    "zone": random.choice(["Zone-A","Zone-B","Zone-C","Zone-D"]),
                }

    async def run(self):
        await self.start()
        # Seed initial sightings
        await self._publish_stats()
        while self._running:
            try:
                latest = await get_cache("vision:latest") or []
                for det in latest:
                    if det.get("class") in POPULATION:
                        await self._record(det)
                await self._publish_stats()
                await asyncio.sleep(6)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"WildlifeAgent error: {e}")
                await asyncio.sleep(10)

    async def _record(self, det: dict):
        species = det["class"]
        # Try to match existing animal by proximity
        matched = None
        for aid, animal in self.registry.items():
            if animal["species"] == species:
                dist = abs(animal["last_lat"] - det.get("lat", 11.4916)) + \
                       abs(animal["last_lon"] - det.get("lon", 76.9294))
                if dist < 0.05:
                    matched = aid
                    break
        if not matched:
            matched = f"{species[:3].upper()}-{uuid.uuid4().hex[:6].upper()}"
            self.registry[matched] = {
                "id": matched, "species": species,
                "first_seen": datetime.now(timezone.utc).isoformat(),
                "sighting_count": 0, "zone": det.get("zone","Unknown")
            }
        animal = self.registry[matched]
        animal["last_seen"]  = datetime.now(timezone.utc).isoformat()
        animal["last_lat"]   = det.get("lat", 11.4916)
        animal["last_lon"]   = det.get("lon", 76.9294)
        animal["zone"]       = det.get("zone", animal.get("zone","Unknown"))
        animal["sighting_count"] = animal.get("sighting_count", 0) + 1
        self.counts[species] += 1
        sighting = {
            "animal_id": matched, "species": species,
            "lat": animal["last_lat"], "lon": animal["last_lon"],
            "zone": animal["zone"],
            "confidence": det.get("confidence", 0.85),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.sightings = (self.sightings + [sighting])[-500:]
        await self.emit("wildlife:sighting_recorded", sighting)

    async def _publish_stats(self):
        stats = {
            sp: {**data, "today_sightings": self.counts[sp]}
            for sp, data in POPULATION.items()
        }
        await set_cache("wildlife:population", stats, expire=120)
        await set_cache("wildlife:registry", dict(list(self.registry.items())[:60]), expire=120)
        await set_cache("wildlife:sightings", self.sightings[-100:], expire=120)

    def heatmap_data(self) -> List[dict]:
        return [{"lat": s["lat"], "lon": s["lon"],
                 "weight": s.get("confidence", 0.8), "species": s["species"]}
                for s in self.sightings[-200:]]
