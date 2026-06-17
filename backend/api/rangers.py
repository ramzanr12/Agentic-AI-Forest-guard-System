"""Rangers API."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from core.database import get_db
from core.security import get_current_user
from core.redis_client import get_cache
from models.models import Ranger, User, RangerDispatch

router = APIRouter(prefix="/api/rangers", tags=["rangers"])


@router.get("")
async def list_rangers(db: AsyncSession = Depends(get_db)):
    # Try live cache first
    live = await get_cache("rangers:live")
    if live:
        return live
    result = await db.execute(select(Ranger))
    rangers = result.scalars().all()
    return [{
        "id":r.id,"badge":r.badge_number,"sector":r.sector,
        "lat":r.current_lat,"lon":r.current_lon,
        "is_on_duty":r.is_on_duty,"status":r.status,"phone":r.phone
    } for r in rangers]


@router.get("/on-duty")
async def on_duty(db: AsyncSession = Depends(get_db)):
    live = await get_cache("rangers:live") or []
    return [r for r in live if r.get("is_on_duty")]


@router.patch("/{badge}/location")
async def update_location(badge: str, lat: float, lon: float,
                          db: AsyncSession = Depends(get_db),
                          user: dict = Depends(get_current_user)):
    from datetime import datetime, timezone
    result = await db.execute(select(Ranger).where(Ranger.badge_number == badge))
    r = result.scalars().first()
    if not r:
        raise HTTPException(404, "Ranger not found")
    r.current_lat = lat; r.current_lon = lon
    r.last_updated = datetime.now(timezone.utc)
    await db.commit()
    return {"message":"Location updated"}


@router.post("/{badge}/dispatch")
async def dispatch_ranger(badge: str, alert_id: Optional[int] = None,
                          lat: float = 11.4916, lon: float = 76.9294,
                          db: AsyncSession = Depends(get_db),
                          user: dict = Depends(get_current_user)):
    result = await db.execute(select(Ranger).where(Ranger.badge_number == badge))
    r = result.scalars().first()
    if not r:
        raise HTTPException(404, "Ranger not found")
    from datetime import datetime, timezone
    dispatch = RangerDispatch(
        ranger_id=r.id, alert_id=alert_id,
        incident_lat=lat, incident_lon=lon,
        status="dispatched"
    )
    r.status = "dispatched"
    db.add(dispatch)
    await db.commit()
    return {"message":f"Ranger {badge} dispatched","dispatch_id":dispatch.id}


@router.get("/{badge}/patrol-route")
async def patrol_route(badge: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ranger).where(Ranger.badge_number == badge))
    r = result.scalars().first()
    if not r:
        raise HTTPException(404, "Ranger not found")
    import math
    base_lat, base_lon = r.current_lat, r.current_lon
    route = []
    for i in range(8):
        a = (i/8)*2*math.pi
        route.append({"lat":base_lat+0.02*math.cos(a), "lon":base_lon+0.02*math.sin(a),"wp":i+1})
    route.append(route[0])
    return {"badge":badge,"sector":r.sector,"route":route}
