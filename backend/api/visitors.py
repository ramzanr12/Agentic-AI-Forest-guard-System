"""Visitors API."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional
from core.database import get_db
from core.security import get_current_user
from models.models import Visitor, VisitLog, User

router = APIRouter(prefix="/api/visitors", tags=["visitors"])


class VisitorUpdate(BaseModel):
    permit_type: Optional[str] = None
    vehicle_number: Optional[str] = None
    group_size: Optional[int] = None


@router.get("")
async def list_visitors(db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    if user["role"] not in ("admin", "ranger"):
        raise HTTPException(403, "Access denied")
    result = await db.execute(select(Visitor))
    visitors = result.scalars().all()
    out = []
    for v in visitors:
        u_res = await db.execute(select(User).where(User.id == v.user_id))
        u = u_res.scalars().first()
        out.append({
            "id":v.id,"permit_type":v.permit_type,"vehicle":v.vehicle_number,
            "group_size":v.group_size,"is_inside":v.is_inside,
            "entry_time":v.entry_time.isoformat() if v.entry_time else None,
            "username":u.username if u else "","full_name":u.full_name if u else ""
        })
    return out


@router.get("/stats")
async def visitor_stats(db: AsyncSession = Depends(get_db)):
    total   = (await db.execute(select(func.count()).select_from(Visitor))).scalar()
    inside  = (await db.execute(select(func.count()).select_from(Visitor).where(Visitor.is_inside==True))).scalar()
    overstay= (await db.execute(select(func.count()).select_from(Visitor).where(Visitor.overstay_alerted==True))).scalar()
    return {"total_registered":total,"currently_inside":inside,"overstay_alerts":overstay}


@router.post("/{visitor_id}/entry")
async def log_entry(visitor_id: int, gate: str = "main",
                    db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    result = await db.execute(select(Visitor).where(Visitor.id == visitor_id))
    v = result.scalars().first()
    if not v:
        raise HTTPException(404, "Visitor not found")
    v.is_inside = True
    v.entry_time = datetime.now(timezone.utc)
    v.overstay_alerted = False
    log = VisitLog(visitor_id=v.id, action="entry", gate=gate)
    db.add(log)
    await db.commit()
    # Generate QR
    from agents.visitor_agent import VisitorAgent
    u_res = await db.execute(select(User).where(User.id == v.user_id))
    u = u_res.scalars().first()
    qr = VisitorAgent.generate_qr(v.id, v.permit_type, u.full_name if u else "Visitor")
    v.ticket_qr = qr
    await db.commit()
    return {"message":"Entry logged","qr_base64":qr}


@router.post("/{visitor_id}/exit")
async def log_exit(visitor_id: int, gate: str = "main",
                   db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    result = await db.execute(select(Visitor).where(Visitor.id == visitor_id))
    v = result.scalars().first()
    if not v:
        raise HTTPException(404, "Visitor not found")
    v.is_inside = False
    v.exit_time = datetime.now(timezone.utc)
    log = VisitLog(visitor_id=v.id, action="exit", gate=gate)
    db.add(log)
    await db.commit()
    return {"message":"Exit logged"}


@router.get("/{visitor_id}/qr")
async def get_qr(visitor_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Visitor).where(Visitor.id == visitor_id))
    v = result.scalars().first()
    if not v:
        raise HTTPException(404, "Visitor not found")
    if not v.ticket_qr:
        u_res = await db.execute(select(User).where(User.id == v.user_id))
        u = u_res.scalars().first()
        from agents.visitor_agent import VisitorAgent
        qr = VisitorAgent.generate_qr(v.id, v.permit_type, u.full_name if u else "Visitor")
        v.ticket_qr = qr
        await db.commit()
    return {"qr_base64": v.ticket_qr}
