"""Wildlife API."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from core.database import get_db
from core.redis_client import get_cache
from models.models import AnimalSighting

router = APIRouter(prefix="/api/wildlife", tags=["wildlife"])


@router.get("/population")
async def population():
    data = await get_cache("wildlife:population")
    if data: return data
    from agents.wildlife_agent import POPULATION
    return POPULATION


@router.get("/registry")
async def registry():
    data = await get_cache("wildlife:registry")
    return data or {}


@router.get("/sightings")
async def sightings(
    species: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db)
):
    q = select(AnimalSighting).order_by(desc(AnimalSighting.seen_at)).limit(limit)
    if species:
        q = q.where(AnimalSighting.species == species)
    result = await db.execute(q)
    rows = result.scalars().all()
    return [{
        "id":s.id,"animal_id":s.animal_id,"species":s.species,
        "lat":s.lat,"lon":s.lon,"confidence":s.confidence,
        "zone":s.zone,"seen_at":s.seen_at.isoformat() if s.seen_at else ""
    } for s in rows]


@router.get("/heatmap")
async def heatmap():
    data = await get_cache("wildlife:sightings")
    if not data: return []
    return [{"lat":s["lat"],"lon":s["lon"],
             "weight":s.get("confidence",0.8),"species":s["species"]}
            for s in data]
