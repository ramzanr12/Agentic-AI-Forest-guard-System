"""Logger Agent — system-wide event logging to DB and file."""
import asyncio, logging, os
from datetime import datetime, timezone
from agents.base_agent import BaseAgent
from core.redis_client import get_cache
from core.config import settings


class LoggerAgent(BaseAgent):
    def __init__(self):
        super().__init__("LoggerAgent")
        self._setup_file_logging()

    def _setup_file_logging(self):
        log_path = os.path.join(settings.logs_dir, "events.log")
        fh = logging.FileHandler(log_path)
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        root = logging.getLogger()
        root.setLevel(logging.INFO)
        root.addHandler(fh)

    async def run(self):
        await self.start()
        while self._running:
            try:
                await self._snapshot_state()
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"LoggerAgent error: {e}")
                await asyncio.sleep(30)

    async def _snapshot_state(self):
        state = await get_cache("system:state") or {}
        alerts = await get_cache("alerts:active") or []
        rangers = await get_cache("rangers:live") or []
        on_duty = sum(1 for r in rangers if r.get("is_on_duty"))
        self.logger.info(
            f"SNAPSHOT | alerts={len(alerts)} | rangers_on_duty={on_duty} | "
            f"fire_risk={state.get('fire_risk','?')} | "
            f"visitors={state.get('visitors_inside','?')}"
        )
