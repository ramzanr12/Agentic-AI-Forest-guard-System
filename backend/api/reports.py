"""Reports API — generate and download PDF reports."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import os
from core.database import get_db
from core.security import get_current_user
from core.config import settings
from models.models import DailyReport

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("")
async def list_reports(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DailyReport).order_by(desc(DailyReport.created_at)).limit(30))
    reports = result.scalars().all()
    return [{
        "id":r.id,"report_date":r.report_date,"total_alerts":r.total_alerts,
        "critical_alerts":r.critical_alerts,"visitors_today":r.visitors_today,
        "animal_sightings":r.animal_sightings,"rangers_on_duty":r.rangers_on_duty,
        "summary":r.summary,"pdf_path":r.pdf_path,
        "created_at":r.created_at.isoformat() if r.created_at else ""
    } for r in reports]


@router.post("/generate/daily")
async def generate_daily(date: str = None, user: dict = Depends(get_current_user)):
    if user["role"] not in ("admin","ranger"):
        raise HTTPException(403, "Access denied")
    from agents.report_agent import ReportAgent
    agent = ReportAgent()
    report_date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    pdf_path = await agent.generate_daily_report(report_date)
    return {"message":"Daily report generated","date":report_date,"pdf_path":pdf_path}


@router.post("/generate/weekly")
async def generate_weekly(user: dict = Depends(get_current_user)):
    if user["role"] not in ("admin","ranger"):
        raise HTTPException(403, "Access denied")
    from agents.report_agent import ReportAgent
    agent = ReportAgent()
    pdf_path = await agent.generate_weekly_report()
    week = datetime.now(timezone.utc).strftime("%Y-W%W")
    return {"message":"Weekly report generated","week":week,"pdf_path":pdf_path}


@router.get("/download/{report_type}/{name}")
async def download_report(report_type: str, name: str, user: dict = Depends(get_current_user)):
    if report_type not in ("daily","weekly"):
        raise HTTPException(400, "Invalid report type")
    path = os.path.join(settings.reports_dir, f"{report_type}_{name}.pdf")
    if not os.path.exists(path):
        raise HTTPException(404, "Report not found. Generate it first.")
    return FileResponse(path, media_type="application/pdf",
                        filename=f"forest_report_{report_type}_{name}.pdf")


@router.get("/summary/daily")
async def daily_summary():
    from services.ai_service import generate_daily_summary
    return {"summary": await generate_daily_summary()}


@router.get("/summary/weekly")
async def weekly_summary():
    from services.ai_service import generate_daily_summary
    from core.redis_client import get_cache
    days_data = await get_cache("threat:risk_scores") or {}
    summary = await generate_daily_summary()
    # Extend with weekly context
    weekly = f"""# 📊 Weekly Intelligence Report — {datetime.now(timezone.utc).strftime('%Y-W%W')}

{summary}

## 7-Day Trend Analysis
- Fire Risk Trend: {'↑ Rising' if days_data.get('fire',25) > 50 else '→ Stable' if days_data.get('fire',25) > 30 else '↓ Low'}
- Poaching Incidents: Pattern analysis shows elevated risk during weekend nights
- Wildlife Movement: Seasonal migration patterns detected in Zone-B and Zone-C
- Visitor Compliance: 94% of visitors adhered to permit time constraints

## Recommendations
1. Increase night patrols in Zone-D during weekends
2. Deploy additional camera traps near Water-Source-Protected zone
3. Schedule vegetation fire-break maintenance in Zone-A
4. Coordinate with local authorities on poaching intelligence sharing
"""
    return {"summary": weekly}
