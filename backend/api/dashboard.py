"""Dashboard API — system-wide metrics."""
from fastapi import APIRouter
from core.redis_client import get_cache
from services.weather_service import fetch_weather, fire_risk
from services.news_service import fetch_news

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/overview")
async def overview():
    state   = await get_cache("system:state") or {}
    alerts  = await get_cache("alerts:active") or []
    rangers = await get_cache("rangers:live") or []
    scores  = await get_cache("threat:risk_scores") or {}
    weather = await fetch_weather()
    pop     = await get_cache("wildlife:population") or {}

    on_duty  = sum(1 for r in rangers if r.get("is_on_duty"))
    critical = [a for a in alerts if a.get("severity") in ["critical","high"]]

    return {
        "active_alerts":      len([a for a in alerts if a.get("status")=="active"]),
        "critical_alerts":    len(critical),
        "rangers_on_duty":    on_duty,
        "total_rangers":      len(rangers),
        "visitors_inside":    state.get("visitors_inside", 0),
        "fire_risk":          scores.get("fire", state.get("fire_risk", 25)),
        "poaching_risk":      scores.get("poaching", state.get("poaching_risk", 20)),
        "intrusion_risk":     scores.get("intrusion", 15),
        "weather":            weather,
        "fire_risk_weather":  fire_risk(weather),
        "species_count":      len(pop),
        "system_status":      "operational",
    }


@router.get("/weather")
async def weather():
    w = await fetch_weather()
    w["fire_risk"] = fire_risk(w)
    return w


@router.get("/news")
async def news():
    return await fetch_news()


@router.get("/risk-scores")
async def risk_scores():
    return await get_cache("threat:risk_scores") or {
        "fire":25,"poaching":20,"intrusion":15
    }


@router.get("/geo-zones")
async def geo_zones():
    return await get_cache("geo:zones") or []


@router.get("/map-data")
async def map_data():
    rangers  = await get_cache("rangers:live") or []
    alerts   = await get_cache("alerts:active") or []
    sightings= await get_cache("wildlife:sightings") or []
    zones    = await get_cache("geo:zones") or []
    return {
        "rangers":  rangers,
        "alerts":   alerts[:30],
        "sightings":sightings[:50],
        "zones":    zones
    }
