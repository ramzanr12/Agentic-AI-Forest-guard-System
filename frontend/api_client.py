"""HTTP client for all backend API calls."""
import os
import requests
import streamlit as st
from typing import Optional, Any

BACKEND = os.getenv("BACKEND_URL", "http://localhost:8000")


def _headers(token: Optional[str] = None) -> dict:
    h = {"Content-Type": "application/json"}
    t = token or st.session_state.get("token")
    if t:
        h["Authorization"] = f"Bearer {t}"
    return h


def _get(path: str, params: dict = None, token: str = None) -> Any:
    try:
        r = requests.get(f"{BACKEND}{path}", headers=_headers(token),
                         params=params, timeout=8)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Backend offline. Ensure `docker compose up` is running.")
        return None
    except Exception as e:
        return None


def _post(path: str, data: dict = None, token: str = None) -> Any:
    try:
        r = requests.post(f"{BACKEND}{path}", headers=_headers(token),
                          json=data, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def _patch(path: str, token: str = None) -> Any:
    try:
        r = requests.patch(f"{BACKEND}{path}", headers=_headers(token), timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


# ── Auth ──────────────────────────────────────────────────────────────────
def login(username: str, password: str) -> Optional[dict]:
    try:
        r = requests.post(f"{BACKEND}/api/auth/token",
                          data={"username": username, "password": password},
                          timeout=8)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None


def register(username, email, full_name, password, role) -> Optional[dict]:
    return _post("/api/auth/register", {
        "username": username, "email": email, "full_name": full_name,
        "password": password, "role": role
    })


# ── Dashboard ─────────────────────────────────────────────────────────────
def get_overview()   -> dict: return _get("/api/dashboard/overview") or {}
def get_weather()    -> dict: return _get("/api/dashboard/weather") or {}
def get_risk_scores()-> dict: return _get("/api/dashboard/risk-scores") or {}
def get_map_data()   -> dict: return _get("/api/dashboard/map-data") or {}
def get_geo_zones()  -> list: return _get("/api/dashboard/geo-zones") or []
def get_news()       -> list: return _get("/api/dashboard/news") or []

# ── Alerts ────────────────────────────────────────────────────────────────
def get_alerts(status=None, severity=None) -> list:
    p = {}
    if status: p["status"] = status
    if severity: p["severity"] = severity
    return _get("/api/alerts", params=p) or []

def get_alert_stats() -> dict: return _get("/api/alerts/stats") or {}
def ack_alert(alert_id: int):  return _patch(f"/api/alerts/{alert_id}/acknowledge")
def resolve_alert(alert_id: int): return _patch(f"/api/alerts/{alert_id}/resolve")

def create_alert(data: dict) -> Optional[dict]:
    return _post("/api/alerts", data)

# ── Rangers ───────────────────────────────────────────────────────────────
def get_rangers()     -> list: return _get("/api/rangers") or []
def get_rangers_duty()-> list: return _get("/api/rangers/on-duty") or []

def dispatch_ranger(badge: str, lat: float, lon: float, alert_id: int = None):
    p = {"lat": lat, "lon": lon}
    if alert_id: p["alert_id"] = alert_id
    try:
        r = requests.post(f"{BACKEND}/api/rangers/{badge}/dispatch",
                          headers=_headers(), params=p, timeout=8)
        return r.json() if r.ok else None
    except Exception:
        return None

def get_patrol_route(badge: str) -> dict:
    return _get(f"/api/rangers/{badge}/patrol-route") or {}

# ── Visitors ──────────────────────────────────────────────────────────────
def get_visitors()      -> list: return _get("/api/visitors") or []
def get_visitor_stats() -> dict: return _get("/api/visitors/stats") or {}
def log_entry(vid: int):  return _post(f"/api/visitors/{vid}/entry")
def log_exit(vid: int):   return _post(f"/api/visitors/{vid}/exit")
def get_visitor_qr(vid: int) -> Optional[str]:
    r = _get(f"/api/visitors/{vid}/qr")
    return r.get("qr_base64") if r else None

# ── Volunteers ────────────────────────────────────────────────────────────
def get_volunteers()    -> list: return _get("/api/volunteers") or []
def get_leaderboard()   -> list: return _get("/api/volunteers/leaderboard") or []
def get_vol_reports()   -> list: return _get("/api/volunteers/reports") or []

def submit_vol_report(incident_type, description, lat, lon) -> Optional[dict]:
    return _post("/api/volunteers/reports", {
        "incident_type": incident_type, "description": description,
        "lat": lat, "lon": lon
    })

# ── Wildlife ──────────────────────────────────────────────────────────────
def get_population()  -> dict: return _get("/api/wildlife/population") or {}
def get_registry()    -> dict: return _get("/api/wildlife/registry") or {}
def get_sightings(species=None) -> list:
    p = {"species": species} if species else {}
    return _get("/api/wildlife/sightings", params=p) or []
def get_heatmap()     -> list: return _get("/api/wildlife/heatmap") or []

# ── Reports ───────────────────────────────────────────────────────────────
def get_reports()     -> list: return _get("/api/reports") or []
def get_daily_summary()  -> str:
    r = _get("/api/reports/summary/daily")
    return r.get("summary","") if r else ""
def get_weekly_summary() -> str:
    r = _get("/api/reports/summary/weekly")
    return r.get("summary","") if r else ""
def generate_daily_report(date: str = None) -> Optional[dict]:
    p = {"date": date} if date else {}
    try:
        r = requests.post(f"{BACKEND}/api/reports/generate/daily",
                          headers=_headers(), params=p, timeout=30)
        return r.json() if r.ok else None
    except Exception:
        return None
def generate_weekly_report() -> Optional[dict]:
    try:
        r = requests.post(f"{BACKEND}/api/reports/generate/weekly",
                          headers=_headers(), timeout=30)
        return r.json() if r.ok else None
    except Exception:
        return None

# ── AI ────────────────────────────────────────────────────────────────────
def ai_chat(message: str) -> str:
    r = _post("/api/ai/chat", {"message": message})
    return r.get("response","") if r else "AI service unavailable."

def ai_explain(incident_type, description, zone="Unknown") -> str:
    r = _post("/api/ai/explain", {
        "incident_type": incident_type, "description": description, "zone": zone
    })
    return r.get("explanation","") if r else ""

# ── Routing ───────────────────────────────────────────────────────────────
def get_route(flat, flon, tlat, tlon) -> dict:
    return _get("/api/routing/route", params={
        "from_lat": flat, "from_lon": flon, "to_lat": tlat, "to_lon": tlon
    }) or {}
