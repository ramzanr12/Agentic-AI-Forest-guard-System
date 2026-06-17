"""AI service — chat assistant, summaries, incident explanations."""
import logging
from datetime import datetime, timezone
from core.redis_client import get_cache
from core.config import settings

logger = logging.getLogger(__name__)

_FOREST_KB = {
    "fire": "Forest fire risk is calculated from temperature, humidity, and wind speed. High temps (>35°C) with low humidity (<30%) and strong winds create critical fire conditions.",
    "poaching": "Poaching risk peaks at night (20:00–05:00) and in buffer zones adjacent to roads. Drones and camera traps are key detection tools.",
    "elephant": "Elephants require 18–20 hours per day for foraging and travel up to 80 km daily. They follow fixed corridors between water sources.",
    "tiger": "Tigers are solitary and territorial. Each adult tiger requires 20–100 km² of habitat. They are most active at dawn and dusk.",
    "ranger": "Rangers conduct patrol duties in assigned sectors, respond to alerts within 15–30 minutes, and log all incidents using mobile apps.",
    "permit": "Visitor permits: Day Pass (6:00–18:00), Research Permit (flexible hours with escort), Eco-Tour (guided group visits).",
    "weather": "Forest microclimate varies significantly. Core zone is typically 2–4°C cooler than periphery due to dense canopy cover.",
    "geofence": "Geo-fencing creates virtual perimeters around sensitive zones. Violations trigger automatic alerts and ranger dispatch.",
}


async def chat_response(question: str) -> str:
    """Rule-based + context-aware chat response."""
    q = question.lower()
    # Check knowledge base
    for key, answer in _FOREST_KB.items():
        if key in q:
            return f"📚 **{key.title()} Info:**\n\n{answer}"

    # Context from live data
    state = await get_cache("system:state") or {}
    weather = await get_cache("weather:current") or {}
    scores = await get_cache("threat:risk_scores") or {}

    if any(w in q for w in ["fire risk","fire danger","burn"]):
        fr = scores.get("fire", state.get("fire_risk", 25))
        level = "🔴 CRITICAL" if fr>80 else "🟠 HIGH" if fr>60 else "🟡 MODERATE" if fr>40 else "🟢 LOW"
        return (f"**Current Fire Risk: {level} ({fr}%)**\n\n"
                f"Temp: {weather.get('temperature','N/A')}°C | "
                f"Humidity: {weather.get('humidity','N/A')}% | "
                f"Wind: {weather.get('wind_speed','N/A')} m/s")

    if any(w in q for w in ["poach","illegal","intrusion"]):
        pr = scores.get("poaching", 20)
        return (f"**Poaching Risk: {pr}%**\n\n"
                f"Risk is {'elevated — night patrol recommended' if pr>60 else 'within normal range'}.\n"
                f"Current time-based risk factor applied.")

    if any(w in q for w in ["weather","temperature","rain","humidity"]):
        return (f"**Current Weather:**\n\n"
                f"🌡️ Temperature: {weather.get('temperature','N/A')}°C\n"
                f"💧 Humidity: {weather.get('humidity','N/A')}%\n"
                f"💨 Wind: {weather.get('wind_speed','N/A')} m/s\n"
                f"☁️ Conditions: {weather.get('conditions','N/A')}")

    if any(w in q for w in ["ranger","patrol","dispatch","duty"]):
        rangers = await get_cache("rangers:live") or []
        on_duty = sum(1 for r in rangers if r.get("is_on_duty"))
        return (f"**Ranger Status:**\n\n"
                f"👮 Rangers on duty: {on_duty}/{len(rangers)}\n"
                f"Sectors covered: Zone-A, Zone-B, Zone-C, Zone-D, Core-Zone\n"
                f"Emergency dispatch available 24/7.")

    if any(w in q for w in ["alert","incident","emergency"]):
        alerts = await get_cache("alerts:active") or []
        return (f"**Active Alerts: {len(alerts)}**\n\n"
                + "\n".join(f"• [{a.get('severity','?').upper()}] {a.get('description','')[:80]}"
                            for a in alerts[:5]))

    if any(w in q for w in ["animal","wildlife","sighting","species"]):
        pop = await get_cache("wildlife:population") or {}
        lines = "\n".join(
            f"{d.get('icon','🐾')} {sp.title()}: {d.get('count','?')} (Trend: {d.get('trend','?')})"
            for sp, d in list(pop.items())[:5]
        )
        return f"**Wildlife Population:**\n\n{lines}"

    # Default helpful response
    return (f"I'm the Forest Intelligence Assistant for **{settings.forest_name}**.\n\n"
            f"I can help with:\n"
            f"• 🔥 Fire risk & weather\n"
            f"• 🦁 Wildlife & animal tracking\n"
            f"• 👮 Ranger operations\n"
            f"• 🚨 Alerts & incidents\n"
            f"• 🗺️ Zones & geo-fencing\n"
            f"• 🎫 Visitor permits\n\n"
            f"Ask me anything about forest management!")


async def generate_daily_summary() -> str:
    state = await get_cache("system:state") or {}
    alerts = await get_cache("alerts:active") or []
    weather = await get_cache("weather:current") or {}
    scores = await get_cache("threat:risk_scores") or {}
    pop = await get_cache("wildlife:population") or {}
    rangers = await get_cache("rangers:live") or []

    critical = [a for a in alerts if a.get("severity") in ["critical","high"]]
    on_duty = sum(1 for r in rangers if r.get("is_on_duty"))
    top_species = sorted(pop.items(), key=lambda x: x[1].get("today_sightings",0), reverse=True)

    summary = f"""## 🌿 Daily Forest Intelligence Summary
**{datetime.now(timezone.utc).strftime('%A, %d %B %Y')} | {settings.forest_name}**

---
### 📊 Operational Status
- **Active Alerts:** {len(alerts)} ({len(critical)} critical)
- **Rangers On Duty:** {on_duty}/{len(rangers)}
- **Visitors Inside:** {state.get('visitors_inside', 'N/A')}
- **Fire Risk:** {scores.get('fire', state.get('fire_risk', 25)):.1f}%
- **Poaching Risk:** {scores.get('poaching', state.get('poaching_risk', 20)):.1f}%

### 🌡️ Weather
- Temperature: {weather.get('temperature','N/A')}°C | Humidity: {weather.get('humidity','N/A')}%
- Wind: {weather.get('wind_speed','N/A')} m/s | Conditions: {weather.get('conditions','N/A')}

### 🦁 Top Wildlife Activity
{chr(10).join(f"- {pop.get(sp,{}).get('icon','🐾')} **{sp.title()}**: {d.get('today_sightings',0)} sightings today" for sp,d in top_species[:4])}

### 🚨 Recent Critical Alerts
{chr(10).join(f"- [{a.get('zone','?')}] {a.get('description','')[:100]}" for a in critical[:3]) or "- No critical alerts"}

---
*Summary generated at {datetime.now(timezone.utc).strftime('%H:%M UTC')}*
"""
    return summary


async def explain_incident(incident_type: str, description: str, zone: str) -> str:
    scores = await get_cache("threat:risk_scores") or {}
    weather = await get_cache("weather:current") or {}
    explanations = {
        "fire": (f"🔥 **Fire Incident Analysis**\n\n"
                 f"**Zone:** {zone}\n"
                 f"**Description:** {description}\n\n"
                 f"**Contributing Factors:**\n"
                 f"- Temperature: {weather.get('temperature','N/A')}°C (threshold: >35°C)\n"
                 f"- Humidity: {weather.get('humidity','N/A')}% (danger below 30%)\n"
                 f"- Wind: {weather.get('wind_speed','N/A')} m/s\n\n"
                 f"**Current Fire Risk Score:** {scores.get('fire',25):.1f}%\n\n"
                 f"**Recommended Actions:** Dispatch nearest ranger, alert fire brigade (101), "
                 f"evacuate visitors within 2km radius."),
        "poaching": (f"🎯 **Poaching Incident Analysis**\n\n"
                     f"**Zone:** {zone}\n"
                     f"**Description:** {description}\n\n"
                     f"**Risk Level:** {scores.get('poaching',20):.1f}%\n\n"
                     f"**Recommended Actions:** Dispatch 2 rangers minimum, activate camera traps, "
                     f"alert district forest officer, document evidence."),
        "intrusion": (f"🚨 **Intrusion Alert Analysis**\n\n"
                      f"**Zone:** {zone}\n**Description:** {description}\n\n"
                      f"**Recommended Actions:** Dispatch nearest ranger, check vehicle registration, "
                      f"verify permits, issue warning or detain if necessary."),
    }
    return explanations.get(incident_type,
        f"📋 **Incident Analysis — {incident_type.title()}**\n\n"
        f"**Zone:** {zone}\n**Description:** {description}\n\n"
        f"Escalate to duty ranger for on-ground assessment.")
