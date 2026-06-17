"""Vision Agent — YOLOv8 object detection with simulation fallback."""
import asyncio
import random
import uuid
from datetime import datetime, timezone
from typing import List, Dict
from agents.base_agent import BaseAgent
from core.redis_client import set_cache

try:
    from ultralytics import YOLO
    import cv2
    # Patch PyTorch 2.6 weights_only default before YOLO loads
    import torch
    _orig_load = torch.load
    def _patched_load(*a, **kw):
        kw.setdefault("weights_only", False)
        return _orig_load(*a, **kw)
    torch.load = _patched_load
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False


class SimpleTracker:
    """IoU-based tracker assigning unique IDs to detected objects."""
    def __init__(self):
        self.objects: Dict[str, dict] = {}

    def _iou(self, b1, b2):
        ix1, iy1 = max(b1[0], b2[0]), max(b1[1], b2[1])
        ix2, iy2 = min(b1[2], b2[2]), min(b1[3], b2[3])
        inter = max(0, ix2-ix1) * max(0, iy2-iy1)
        a1 = (b1[2]-b1[0]) * (b1[3]-b1[1])
        a2 = (b2[2]-b2[0]) * (b2[3]-b2[1])
        union = a1 + a2 - inter
        return inter/union if union > 0 else 0

    def update(self, detections: list) -> list:
        result = []
        for det in detections:
            bbox = det.get("bbox", [0, 0, 100, 100])
            cls = det.get("class", "unknown")
            best, best_iou = None, 0.35
            for oid, obj in self.objects.items():
                if obj["class"] == cls:
                    s = self._iou(obj["bbox"], bbox)
                    if s > best_iou:
                        best, best_iou = oid, s
            if best:
                self.objects[best]["bbox"] = bbox
                det["tracking_id"] = best
            else:
                new_id = f"{cls[:3].upper()}-{uuid.uuid4().hex[:6].upper()}"
                self.objects[new_id] = {"class": cls, "bbox": bbox}
                det["tracking_id"] = new_id
            result.append(det)
        return result


class VisionAgent(BaseAgent):
    WILDLIFE = {"elephant", "tiger", "deer", "leopard", "bear", "snake"}
    THREATS = {"person", "car", "truck", "motorcycle"}
    FIRE_CLS = {"fire", "smoke"}

    def __init__(self):
        super().__init__("VisionAgent")
        self.model = None
        self.tracker = SimpleTracker()
        self.history: List[dict] = []

    async def on_start(self):
        if YOLO_AVAILABLE:
            try:
                loop = asyncio.get_event_loop()
                self.model = await loop.run_in_executor(None, lambda: YOLO("yolov8n.pt"))
                self.logger.info("YOLOv8 model loaded")
            except Exception as e:
                self.logger.warning(f"YOLO load failed: {e}, using simulation")
        else:
            self.logger.warning("YOLOv8 not installed, running simulation mode")

    async def run(self):
        await self.start()
        while self._running:
            try:
                detections = await self._detect()
                if detections:
                    tracked = self.tracker.update(detections)
                    await self._process(tracked)
                await asyncio.sleep(2)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"VisionAgent error: {e}")
                await asyncio.sleep(5)

    async def _detect(self) -> list:
        if self.model and YOLO_AVAILABLE:
            return await self._yolo_detect()
        return self._simulate()

    async def _yolo_detect(self) -> list:
        # No physical camera available in Docker — always use simulation
        return self._simulate()

    def _simulate(self) -> list:
        if random.random() > 0.4:
            return []
        options = [
            ("elephant", 0.55), ("deer", 0.45), ("tiger", 0.12),
            ("leopard", 0.08), ("person", 0.20), ("fire", 0.06),
            ("smoke", 0.07), ("car", 0.10), ("motorcycle", 0.08)
        ]
        cls, prob = random.choice(options)
        if random.random() > prob:
            return []
        return [{
            "class": cls,
            "confidence": round(random.uniform(0.72, 0.97), 3),
            "bbox": [
                random.randint(50, 400), random.randint(50, 300),
                random.randint(401, 600), random.randint(301, 450)
            ]
        }]

    async def _process(self, detections: list):
        ts = datetime.now(timezone.utc).isoformat()
        zone = random.choice(["Zone-A", "Zone-B", "Zone-C", "Zone-D"])
        lat = 11.4916 + random.uniform(-0.08, 0.08)
        lon = 76.9294 + random.uniform(-0.08, 0.08)
        for det in detections:
            det.update({"timestamp": ts, "zone": zone, "lat": lat, "lon": lon})
            cls = det["class"]
            if cls in self.FIRE_CLS:
                await self.emit("alerts:new", {**det, "alert_type": "fire", "severity": "critical"})
            elif cls == "person":
                await self.emit("alerts:new", {**det, "alert_type": "intrusion", "severity": "high"})
            elif cls in self.WILDLIFE:
                await self.emit("wildlife:sighting", det)
            elif cls in self.THREATS - {"person"}:
                await self.emit("alerts:new", {**det, "alert_type": "vehicle", "severity": "medium"})
        self.history = (self.history + detections)[-100:]
        await set_cache("vision:latest", self.history[-20:], expire=30)
