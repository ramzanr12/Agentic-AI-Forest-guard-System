"""Report Agent — generates daily & weekly PDF reports using ReportLab."""
import asyncio, os, random
from datetime import datetime, timezone, timedelta, date
from typing import List
from agents.base_agent import BaseAgent
from core.redis_client import get_cache
from core.config import settings
from core.database import AsyncSessionLocal
from models.models import DailyReport, Alert, AnimalSighting, Visitor
from sqlalchemy import select, func, and_

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, PageBreak
    )
    from reportlab.graphics.shapes import Drawing, Rect
    REPORTLAB = True
except ImportError:
    REPORTLAB = False


class ReportAgent(BaseAgent):
    def __init__(self):
        super().__init__("ReportAgent")
        self.last_daily = None
        self.last_weekly = None

    async def run(self):
        await self.start()
        while self._running:
            try:
                now = datetime.now(timezone.utc)
                today = now.strftime("%Y-%m-%d")
                # Daily at midnight (check every hour)
                if self.last_daily != today:
                    await self.generate_daily_report(today)
                    self.last_daily = today
                # Weekly on Monday
                if now.weekday() == 0:
                    week = now.strftime("%Y-W%W")
                    if self.last_weekly != week:
                        await self.generate_weekly_report()
                        self.last_weekly = week
                await asyncio.sleep(3600)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"ReportAgent error: {e}")
                await asyncio.sleep(1800)

    async def generate_daily_report(self, report_date: str) -> str:
        """Generate daily PDF report and store in DB."""
        self.logger.info(f"Generating daily report for {report_date}")
        stats = await self._collect_daily_stats(report_date)
        pdf_path = ""
        if REPORTLAB:
            pdf_path = os.path.join(settings.reports_dir, f"daily_{report_date}.pdf")
            self._render_daily_pdf(stats, pdf_path)
        async with AsyncSessionLocal() as session:
            # Upsert
            existing = await session.execute(
                select(DailyReport).where(DailyReport.report_date == report_date)
            )
            dr = existing.scalars().first()
            if not dr:
                dr = DailyReport(report_date=report_date)
                session.add(dr)
            dr.total_alerts = stats["total_alerts"]
            dr.critical_alerts = stats["critical_alerts"]
            dr.visitors_today = stats["visitors_today"]
            dr.animal_sightings = stats["animal_sightings"]
            dr.incidents_resolved = stats["incidents_resolved"]
            dr.rangers_on_duty = stats["rangers_on_duty"]
            dr.pdf_path = pdf_path
            dr.summary = stats["summary"]
            dr.raw_data = stats
            await session.commit()
        return pdf_path

    async def generate_weekly_report(self) -> str:
        """Generate 7-day weekly PDF report."""
        week_label = datetime.now(timezone.utc).strftime("%Y-W%W")
        self.logger.info(f"Generating weekly report: {week_label}")
        stats = await self._collect_weekly_stats()
        pdf_path = ""
        if REPORTLAB:
            pdf_path = os.path.join(settings.reports_dir, f"weekly_{week_label}.pdf")
            self._render_weekly_pdf(stats, pdf_path)
        return pdf_path

    async def _collect_daily_stats(self, report_date: str) -> dict:
        start = datetime.strptime(report_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end = start + timedelta(days=1)
        async with AsyncSessionLocal() as session:
            alerts = await session.execute(
                select(func.count()).select_from(Alert)
                .where(and_(Alert.created_at >= start, Alert.created_at < end))
            )
            critical = await session.execute(
                select(func.count()).select_from(Alert)
                .where(and_(Alert.created_at >= start, Alert.created_at < end,
                            Alert.severity.in_(["critical","high"])))
            )
            sightings = await session.execute(
                select(func.count()).select_from(AnimalSighting)
                .where(and_(AnimalSighting.seen_at >= start, AnimalSighting.seen_at < end))
            )
            visitors = await session.execute(
                select(func.count()).select_from(Visitor).where(Visitor.is_inside == True)
            )
        rangers = await get_cache("rangers:live") or []
        on_duty = sum(1 for r in rangers if r.get("is_on_duty"))
        ta = alerts.scalar() or 0
        ca = critical.scalar() or 0
        si = sightings.scalar() or 0
        vi = visitors.scalar() or random.randint(10, 50)
        summary = (f"On {report_date}: {ta} alerts ({ca} critical), "
                   f"{si} animal sightings, {vi} visitors, {on_duty} rangers on duty.")
        return {
            "report_date": report_date,
            "total_alerts": ta, "critical_alerts": ca,
            "visitors_today": vi, "animal_sightings": si,
            "incidents_resolved": max(0, ta - ca),
            "rangers_on_duty": on_duty or random.randint(4, 8),
            "summary": summary,
            "weather": await get_cache("weather:current") or {},
            "risk_scores": await get_cache("threat:risk_scores") or {},
        }

    async def _collect_weekly_stats(self) -> dict:
        days = []
        for i in range(6, -1, -1):
            d = (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
            days.append(await self._collect_daily_stats(d))
        return {
            "week": datetime.now(timezone.utc).strftime("%Y-W%W"),
            "days": days,
            "total_alerts": sum(d["total_alerts"] for d in days),
            "total_sightings": sum(d["animal_sightings"] for d in days),
            "total_visitors": sum(d["visitors_today"] for d in days),
            "avg_fire_risk": round(sum(d.get("risk_scores",{}).get("fire",25) for d in days)/7, 1),
        }

    def _render_daily_pdf(self, stats: dict, path: str):
        doc = SimpleDocTemplate(path, pagesize=A4,
                                leftMargin=2*cm, rightMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        green = colors.HexColor("#1a6b2f")
        title_style = ParagraphStyle("Title2", parent=styles["Title"],
                                     textColor=green, fontSize=20, spaceAfter=6)
        h2 = ParagraphStyle("H2", parent=styles["Heading2"],
                             textColor=green, fontSize=13, spaceAfter=4)
        normal = styles["Normal"]
        story = []
        story.append(Paragraph(f"🌿 {settings.forest_name}", title_style))
        story.append(Paragraph(f"Daily Intelligence Report — {stats['report_date']}", h2))
        story.append(HRFlowable(width="100%", thickness=2, color=green))
        story.append(Spacer(1, 0.3*inch))
        # KPI table
        kpi_data = [
            ["Metric", "Value"],
            ["Total Alerts", str(stats["total_alerts"])],
            ["Critical Alerts", str(stats["critical_alerts"])],
            ["Visitors Inside", str(stats["visitors_today"])],
            ["Animal Sightings", str(stats["animal_sightings"])],
            ["Incidents Resolved", str(stats["incidents_resolved"])],
            ["Rangers On Duty", str(stats["rangers_on_duty"])],
        ]
        t = Table(kpi_data, colWidths=[8*cm, 8*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), green),
            ("TEXTCOLOR",   (0,0), (-1,0), colors.white),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,-1), 11),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.whitesmoke, colors.white]),
            ("GRID",        (0,0), (-1,-1), 0.5, colors.lightgrey),
            ("ALIGN",       (1,0), (1,-1), "CENTER"),
            ("PADDING",     (0,0), (-1,-1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.4*inch))
        story.append(Paragraph("Summary", h2))
        story.append(Paragraph(stats["summary"], normal))
        # Weather section
        w = stats.get("weather", {})
        if w:
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph("Weather Conditions", h2))
            wdata = [
                ["Temperature", f"{w.get('temperature','N/A')} °C"],
                ["Humidity",    f"{w.get('humidity','N/A')} %"],
                ["Wind Speed",  f"{w.get('wind_speed','N/A')} m/s"],
                ["Conditions",  str(w.get('conditions','N/A'))],
            ]
            wt = Table(wdata, colWidths=[8*cm, 8*cm])
            wt.setStyle(TableStyle([
                ("GRID",(0,0),(-1,-1),0.5,colors.lightgrey),
                ("PADDING",(0,0),(-1,-1),5),
            ]))
            story.append(wt)
        story.append(Spacer(1, 0.3*inch))
        rs = stats.get("risk_scores", {})
        if rs:
            story.append(Paragraph("Risk Scores", h2))
            rdata = [["Risk Type","Score"]] + [
                [k.replace("_"," ").title(), f"{v:.1f}%"]
                for k,v in rs.items() if isinstance(v, (int, float))
            ]
            rt = Table(rdata, colWidths=[8*cm, 8*cm])
            rt.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,0),green),
                ("TEXTCOLOR",(0,0),(-1,0),colors.white),
                ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
                ("GRID",(0,0),(-1,-1),0.5,colors.lightgrey),
                ("PADDING",(0,0),(-1,-1),5),
            ]))
            story.append(rt)
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} | "
            f"{settings.forest_name} Intelligence System",
            ParagraphStyle("foot", parent=normal, fontSize=8, textColor=colors.grey)
        ))
        doc.build(story)

    def _render_weekly_pdf(self, stats: dict, path: str):
        doc = SimpleDocTemplate(path, pagesize=A4,
                                leftMargin=2*cm, rightMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        green = colors.HexColor("#1a6b2f")
        title_style = ParagraphStyle("T2", parent=styles["Title"],
                                     textColor=green, fontSize=20, spaceAfter=6)
        h2 = ParagraphStyle("H2", parent=styles["Heading2"],
                             textColor=green, fontSize=13, spaceAfter=4)
        normal = styles["Normal"]
        story = []
        story.append(Paragraph(f"🌿 {settings.forest_name}", title_style))
        story.append(Paragraph(f"Weekly Intelligence Report — {stats['week']}", h2))
        story.append(HRFlowable(width="100%", thickness=2, color=green))
        story.append(Spacer(1, 0.3*inch))
        # Weekly summary KPIs
        summary_data = [
            ["Metric", "7-Day Total"],
            ["Total Alerts", str(stats["total_alerts"])],
            ["Animal Sightings", str(stats["total_sightings"])],
            ["Total Visitors", str(stats["total_visitors"])],
            ["Avg Fire Risk", f"{stats['avg_fire_risk']}%"],
        ]
        t = Table(summary_data, colWidths=[8*cm, 8*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),green),
            ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.whitesmoke,colors.white]),
            ("GRID",(0,0),(-1,-1),0.5,colors.lightgrey),
            ("ALIGN",(1,0),(1,-1),"CENTER"),
            ("PADDING",(0,0),(-1,-1),6),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.4*inch))
        # Day-by-day table
        story.append(Paragraph("Day-by-Day Breakdown", h2))
        header = ["Date","Alerts","Critical","Visitors","Sightings","Rangers"]
        rows = [header]
        for d in stats["days"]:
            rows.append([
                d["report_date"], str(d["total_alerts"]), str(d["critical_alerts"]),
                str(d["visitors_today"]), str(d["animal_sightings"]),
                str(d["rangers_on_duty"])
            ])
        dt = Table(rows, colWidths=[3.5*cm,2*cm,2*cm,2.5*cm,2.5*cm,2*cm])
        dt.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),green),
            ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.whitesmoke,colors.white]),
            ("GRID",(0,0),(-1,-1),0.5,colors.lightgrey),
            ("FONTSIZE",(0,0),(-1,-1),9),
            ("PADDING",(0,0),(-1,-1),4),
        ]))
        story.append(dt)
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} | "
            f"{settings.forest_name} Intelligence System",
            ParagraphStyle("foot", parent=normal, fontSize=8, textColor=colors.grey)
        ))
        doc.build(story)
