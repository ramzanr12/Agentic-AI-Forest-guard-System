"""Weather service — OpenWeather API with fallback simulation."""
import random, httpx, logging
from datetime import datetime, timezone
from core.config import settings
from core.redis_client import set_cache, get_cache

logger = logging.getLogger(__name__)


def _sim() -> dict:
    return {
        "temperature": round(random.uniform(22, 38), 1),
        "feels_like":  round(random.uniform(24, 42), 1),
        "humidity":    random.randint(35, 85),
        "wind_speed":  round(random.uniform(2, 20), 1),
        "wind_direction": random.randint(0, 360),
        "conditions":  random.choice(["Clear","Partly Cloudy","Hazy","Sunny","Overcast"]),
        "visibility":  round(random.uniform(5, 15), 1),
        "uv_index":    random.randint(1, 11),
        "pressure":    round(random.uniform(1005, 1020), 1),
        "source": "simulation",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }


async def fetch_weather() -> dict:
    cached = await get_cache("weather:current")
    if cached:
        return cached
    if settings.openweather_api_key in ("demo", "your_openweather_api_key_here", ""):
        data = _sim()
        await set_cache("weather:current", data, expire=600)
        return data
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"lat": settings.forest_center_lat, "lon": settings.forest_center_lon,
              "appid": settings.openweather_api_key, "units": "metric"}
    try:
        async with httpx.AsyncClient(timeout=8) as c:
            r = await c.get(url, params=params); r.raise_for_status()
            raw = r.json()
            data = {
                "temperature": raw["main"]["temp"],
                "feels_like":  raw["main"]["feels_like"],
                "humidity":    raw["main"]["humidity"],
                "wind_speed":  raw["wind"]["speed"],
                "wind_direction": raw["wind"].get("deg",0),
                "conditions":  raw["weather"][0]["description"].title(),
                "visibility":  raw.get("visibility",10000)/1000,
                "pressure":    raw["main"]["pressure"],
                "source": "openweathermap",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            await set_cache("weather:current", data, expire=600)
            return data
    except Exception as e:
        logger.warning(f"Weather API error: {e}")
        data = _sim()
        await set_cache("weather:current", data, expire=300)
        return data


def fire_risk(w: dict) -> float:
    tf = min(100, max(0, (w.get("temperature",28) - 20) * 3))
    hf = max(0, 100 - w.get("humidity",60))
    wf = min(100, w.get("wind_speed",10) * 3)
    return round(0.45*tf + 0.35*hf + 0.20*wf, 1)
