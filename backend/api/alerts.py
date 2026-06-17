"""Alerts API."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional
from core.database import get_db
from core.security import get_current_user
from core.redis_client import get_cache, set_cache
from models.models import Alert

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


class AlertCreate(BaseModel):
    alert_type: str
    severity: str = "medium"
    lat: float
    lon: float
    zone: str = "Unknown"
    description: str = ""
    confidence: float = 0.8


@router.get("")
async def list_alerts(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db)
):
    cached = await get_cache("alerts:active")
    if cached and not status and not severity:
        return cached

    q = select(Alert).order_by(desc(Alert.created_at)).limit(limit)
    if status:
        q = q.where(Alert.status == status)
    if severity:
        q = q.where(Alert.severity == severity)
    result = await db.execute(q)
    alerts = result.scalars().all()
    data = [{
        "id":a.id,"alert_type":a.alert_type,"severity":a.severity,
        "status":a.status,"lat":a.lat,"lon":a.lon,"zone":a.zone,
        "description":a.description,"confidence":a.confidence,
        "source":a.source,
        "created_at":a.created_at.isoformat() if a.created_at else ""
    } for a in alerts]
    await set_cache("alerts:active", data, expire=30)
    return data


@router.post("", status_code=201)
async def create_alert(payload: AlertCreate, db: AsyncSession = Depends(get_db),
                       user: dict = Depends(get_current_user)):
    a = Alert(**payload.model_dump(), source=user["role"])
    db.add(a)
    await db.commit()
    await db.refresh(a)
    await set_cache("alerts:active", None, expire=1)  # invalidate
    return {"id":a.id,"message":"Alert created"}


@router.patch("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int, db: AsyncSession = Depends(get_db),
                            user: dict = Depends(get_current_user)):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    a = result.scalars().first()
    if not a:
        raise HTTPException(404, "Alert not found")
    a.status = "acknowledged"
    a.acknowledged_at = datetime.now(timezone.utc)
    a.acknowledged_by = user["username"]
    await db.commit()
    return {"message":"Alert acknowledged"}


@router.patch("/{alert_id}/resolve")
async def resolve_alert(alert_id: int, db: AsyncSession = Depends(get_db),
                        user: dict = Depends(get_current_user)):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    a = result.scalars().first()
    if not a:
        raise HTTPException(404, "Alert not found")
    a.status = "resolved"
    a.resolved_at = datetime.now(timezone.utc)
    await db.commit()
    return {"message":"Alert resolved"}


@router.get("/stats")
async def alert_stats(db: AsyncSession = Depends(get_db)):
    total   = (await db.execute(select(func.count()).select_from(Alert))).scalar()
    active  = (await db.execute(select(func.count()).select_from(Alert).where(Alert.status=="active"))).scalar()
    critical= (await db.execute(select(func.count()).select_from(Alert).where(Alert.severity=="critical"))).scalar()
    return {"total":total,"active":active,"critical":critical,"resolved":total-active}
