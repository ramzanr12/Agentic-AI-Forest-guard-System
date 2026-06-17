"""Visitor Agent — entry/exit tracking, overstay detection, QR generation."""
import asyncio, qrcode, io, base64, random
from datetime import datetime, timezone, timedelta
from agents.base_agent import BaseAgent
from core.redis_client import set_cache, get_cache
from core.database import AsyncSessionLocal
from core.config import settings
from models.models import Visitor, VisitLog
from sqlalchemy import select


class VisitorAgent(BaseAgent):
    def __init__(self):
        super().__init__("VisitorAgent")

    async def run(self):
        await self.start()
        while self._running:
            try:
                await self._check_overstay()
                await self._refresh_cache()
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"VisitorAgent error: {e}")
                await asyncio.sleep(20)

    async def _check_overstay(self):
        threshold = timedelta(hours=settings.overstay_hours)
        now = datetime.now(timezone.utc)
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Visitor).where(Visitor.is_inside == True, Visitor.overstay_alerted == False)
            )
            visitors = result.scalars().all()
            for v in visitors:
                if v.entry_time and (now - v.entry_time.replace(tzinfo=timezone.utc)) > threshold:
                    v.overstay_alerted = True
                    await self.emit("alerts:new",{
                        "alert_type":"overstay","severity":"medium",
                        "description":f"Visitor #{v.id} has exceeded permitted stay time.",
                        "lat":11.4916 + random.uniform(-0.03,0.03),
                        "lon":76.9294 + random.uniform(-0.03,0.03),
                        "zone":"Entry-Gate"
                    })
            await session.commit()

    async def _refresh_cache(self):
        async with AsyncSessionLocal() as session:
            from sqlalchemy import func
            inside = await session.execute(
                select(func.count()).select_from(Visitor).where(Visitor.is_inside == True)
            )
            count = inside.scalar() or 0
            await set_cache("visitors:inside_count", count, expire=60)

    @staticmethod
    def generate_qr(visitor_id: int, permit_type: str, full_name: str) -> str:
        """Generate base64-encoded QR code for visitor ticket."""
        data = (f"FOREST-GUARD-TICKET\nID:{visitor_id}\n"
                f"Name:{full_name}\nPermit:{permit_type}\n"
                f"Date:{datetime.now(timezone.utc).strftime('%Y-%m-%d')}")
        qr = qrcode.QRCode(version=1, box_size=6, border=2)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#1a6b2f", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")
