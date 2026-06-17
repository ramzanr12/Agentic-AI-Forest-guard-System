"""Volunteers API."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
import os, uuid
from core.database import get_db
from core.security import get_current_user
from core.config import settings
from models.models import Volunteer, VolunteerReport, User

router = APIRouter(prefix="/api/volunteers", tags=["volunteers"])


class ReportCreate(BaseModel):
    incident_type: str
    description: str
    lat: float
    lon: float


@router.get("")
async def list_volunteers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Volunteer).order_by(Volunteer.points.desc()))
    vols = result.scalars().all()
    out = []
    for v in vols:
        u_res = await db.execute(select(User).where(User.id == v.user_id))
        u = u_res.scalars().first()
        out.append({
            "id":v.id,"points":v.points,"zone":v.zone_assigned,
            "skills":v.skills,"verified":v.is_verified,
            "username":u.username if u else "","full_name":u.full_name if u else ""
        })
    return out


@router.get("/leaderboard")
async def leaderboard(db: AsyncSession = Depends(get_db)):
    from core.redis_client import get_cache
    cached = await get_cache("volunteer:leaderboard")
    if cached:
        return cached
    result = await db.execute(select(Volunteer).order_by(Volunteer.points.desc()).limit(10))
    vols = result.scalars().all()
    out = []
    for v in vols:
        u_res = await db.execute(select(User).where(User.id == v.user_id))
        u = u_res.scalars().first()
        out.append({"id":v.id,"full_name":u.full_name if u else "","points":v.points,
                    "zone":v.zone_assigned,"verified":v.is_verified})
    return out


@router.post("/reports", status_code=201)
async def create_report(payload: ReportCreate,
                        db: AsyncSession = Depends(get_db),
                        user: dict = Depends(get_current_user)):
    vol_res = await db.execute(
        select(Volunteer).join(User).where(User.username == user["username"])
    )
    vol = vol_res.scalars().first()
    if not vol:
        raise HTTPException(404, "Volunteer profile not found")
    rep = VolunteerReport(
        volunteer_id=vol.id, incident_type=payload.incident_type,
        description=payload.description, lat=payload.lat, lon=payload.lon
    )
    db.add(rep)
    await db.commit()
    await db.refresh(rep)
    return {"id":rep.id,"message":"Report submitted","status":"pending"}


@router.post("/reports/{report_id}/upload-image")
async def upload_image(report_id: int, file: UploadFile = File(...),
                       db: AsyncSession = Depends(get_db),
                       user: dict = Depends(get_current_user)):
    result = await db.execute(select(VolunteerReport).where(VolunteerReport.id == report_id))
    rep = result.scalars().first()
    if not rep:
        raise HTTPException(404, "Report not found")
    ext = file.filename.rsplit(".",1)[-1] if "." in file.filename else "jpg"
    fname = f"vol_report_{report_id}_{uuid.uuid4().hex[:8]}.{ext}"
    fpath = os.path.join(settings.uploads_dir, fname)
    content = await file.read()
    with open(fpath, "wb") as f:
        f.write(content)
    rep.image_path = fpath
    await db.commit()
    return {"message":"Image uploaded","path":fname}


@router.get("/reports")
async def list_reports(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(VolunteerReport).order_by(desc(VolunteerReport.created_at)).limit(30)
    )
    reports = result.scalars().all()
    return [{
        "id":r.id,"incident_type":r.incident_type,"description":r.description[:200],
        "lat":r.lat,"lon":r.lon,"status":r.status,"points":r.points_awarded,
        "created_at":r.created_at.isoformat() if r.created_at else "",
        "image_path":r.image_path
    } for r in reports]
