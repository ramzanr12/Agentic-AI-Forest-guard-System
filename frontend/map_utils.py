"""Map rendering utilities using Folium + OpenStreetMap."""
import folium
from folium.plugins import HeatMap, MarkerCluster, MiniMap
from typing import List, Dict
import json


SEVERITY_COLORS = {
    "critical": "#ef4444",
    "high":     "#f59e0b",
    "medium":   "#3b82f6",
    "low":      "#22c55e",
}

ALERT_ICONS = {
    "fire":           "🔥",
    "fire_risk":      "🔥",
    "poaching":       "🎯",
    "poaching_risk":  "🎯",
    "intrusion":      "🚨",
    "vehicle":        "🚗",
    "overstay":       "⏰",
    "geofence_violation": "⚠️",
    "animal_movement":"🐾",
}


def build_forest_map(
    center_lat: float = 11.4916,
    center_lon: float = 76.9294,
    zoom: int = 12,
    rangers: List[dict] = None,
    alerts: List[dict] = None,
    sightings: List[dict] = None,
    zones: List[dict] = None,
    route: List[dict] = None,
    show_heatmap: bool = False,
) -> folium.Map:
    """Build the full interactive forest map."""

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="OpenStreetMap",
        prefer_canvas=True,
    )

    # Dark tile layer option
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr='&copy; CartoDB',
        name="Dark Mode",
        show=False,
    ).add_to(m)

    MiniMap(toggle_display=True, position="bottomright").add_to(m)

    # ── Forest boundary circle ──────────────────────────────────────
    folium.Circle(
        location=[center_lat, center_lon],
        radius=8000,
        color="#22c55e",
        weight=2,
        fill=True,
        fill_color="#22c55e",
        fill_opacity=0.04,
        popup="Forest Reserve Boundary",
        tooltip="Forest Reserve",
    ).add_to(m)

    # ── Zones (GeoJSON) ──────────────────────────────────────────────
    if zones:
        zone_colors = {
            "low":        ("#22c55e", 0.12),
            "medium":     ("#f59e0b", 0.14),
            "high":       ("#ef4444", 0.16),
            "restricted": ("#7c3aed", 0.20),
        }
        zone_group = folium.FeatureGroup(name="Forest Zones", show=True)
        for z in zones:
            risk = z.get("risk_level", "low")
            color, opacity = zone_colors.get(risk, ("#22c55e", 0.1))
            geojson = z.get("geojson")
            if geojson:
                folium.GeoJson(
                    geojson,
                    name=z["name"],
                    style_function=lambda f, c=color, o=opacity: {
                        "fillColor": c, "color": c,
                        "weight": 2, "fillOpacity": o
                    },
                    tooltip=folium.GeoJsonTooltip(
                        fields=["name", "risk"],
                        aliases=["Zone", "Risk Level"],
                    ),
                ).add_to(zone_group)
        zone_group.add_to(m)

    # ── Rangers ──────────────────────────────────────────────────────
    if rangers:
        ranger_group = folium.FeatureGroup(name="Rangers", show=True)
        for r in rangers:
            lat, lon = r.get("lat", 0), r.get("lon", 0)
            if not lat and not lon:
                continue
            is_duty  = r.get("is_on_duty", False)
            status   = r.get("status", "off_duty")
            color    = "#22c55e" if is_duty else "#6b7280"
            icon_sym = "👮" if is_duty else "😴"
            html = f"""
            <div style="
              background:rgba(10,26,14,0.92);
              border:2px solid {color};
              border-radius:50%;
              width:36px;height:36px;
              display:flex;align-items:center;justify-content:center;
              font-size:16px;
              box-shadow:0 0 10px {color}88;
            ">{icon_sym}</div>"""
            folium.Marker(
                location=[lat, lon],
                icon=folium.DivIcon(html=html, icon_size=(36, 36), icon_anchor=(18, 18)),
                popup=folium.Popup(
                    f"<b style='color:#22c55e'>{r.get('name','Ranger')}</b><br>"
                    f"Badge: {r.get('badge','?')}<br>"
                    f"Sector: {r.get('sector','?')}<br>"
                    f"Status: <b>{status}</b><br>"
                    f"Phone: {r.get('phone','')}",
                    max_width=200
                ),
                tooltip=f"Ranger {r.get('badge','?')} — {status}",
            ).add_to(ranger_group)
        ranger_group.add_to(m)

    # ── Alerts ───────────────────────────────────────────────────────
    if alerts:
        alert_group = folium.FeatureGroup(name="Alerts", show=True)
        for a in alerts:
            lat, lon = a.get("lat", 0), a.get("lon", 0)
            if not lat and not lon:
                continue
            sev   = a.get("severity", "medium")
            atype = a.get("alert_type", "unknown")
            color = SEVERITY_COLORS.get(sev, "#3b82f6")
            icon  = ALERT_ICONS.get(atype, "⚠️")
            html = f"""
            <div style="
              background:rgba(10,26,14,0.92);
              border:2px solid {color};
              border-radius:8px;
              width:34px;height:34px;
              display:flex;align-items:center;justify-content:center;
              font-size:15px;
              box-shadow:0 0 12px {color}99;
              {'animation:flash 1s infinite;' if sev=='critical' else ''}
            ">{icon}</div>"""
            folium.Marker(
                location=[lat, lon],
                icon=folium.DivIcon(html=html, icon_size=(34, 34), icon_anchor=(17, 17)),
                popup=folium.Popup(
                    f"<b style='color:{color}'>[{sev.upper()}] {atype.replace('_',' ').title()}</b><br>"
                    f"Zone: {a.get('zone','?')}<br>"
                    f"{a.get('description','')[:120]}<br>"
                    f"Confidence: {a.get('confidence',0)*100:.0f}%",
                    max_width=220
                ),
                tooltip=f"[{sev.upper()}] {atype}",
            ).add_to(alert_group)
        alert_group.add_to(m)

    # ── Wildlife sightings ────────────────────────────────────────────
    if sightings:
        if show_heatmap:
            heat_data = [[s["lat"], s["lon"], s.get("weight", 0.7)]
                         for s in sightings if s.get("lat") and s.get("lon")]
            if heat_data:
                HeatMap(
                    heat_data,
                    min_opacity=0.3,
                    radius=18,
                    blur=15,
                    gradient={"0.4":"#22c55e44","0.65":"#f59e0b","1":"#ef4444"},
                ).add_to(folium.FeatureGroup(name="Wildlife Heatmap", show=True).add_to(m))
        else:
            wildlife_group = folium.FeatureGroup(name="Wildlife Sightings", show=True)
            species_icons = {
                "elephant":"🐘","tiger":"🐯","deer":"🦌",
                "leopard":"🐆","bear":"🐻","peacock":"🦚"
            }
            cluster = MarkerCluster().add_to(wildlife_group)
            for s in sightings[:80]:
                lat, lon = s.get("lat",0), s.get("lon",0)
                if not lat and not lon: continue
                ico = species_icons.get(s.get("species","?"), "🐾")
                folium.Marker(
                    location=[lat, lon],
                    icon=folium.DivIcon(
                        html=f'<div style="font-size:18px;text-shadow:0 1px 3px #000">{ico}</div>',
                        icon_size=(24, 24), icon_anchor=(12, 12)
                    ),
                    popup=f"<b>{s.get('species','?').title()}</b><br>"
                          f"ID: {s.get('animal_id','?')}<br>"
                          f"Zone: {s.get('zone','?')}<br>"
                          f"Confidence: {s.get('confidence',0)*100:.0f}%",
                    tooltip=f"{ico} {s.get('species','?').title()}",
                ).add_to(cluster)
            wildlife_group.add_to(m)

    # ── Route visualization ───────────────────────────────────────────
    if route and len(route) >= 2:
        coords = [[p["lat"], p["lon"]] for p in route]
        folium.PolyLine(
            coords,
            color="#22c55e",
            weight=4,
            opacity=0.85,
            dash_array="8 4",
            tooltip="Emergency Route (A*)",
        ).add_to(m)
        folium.Marker(
            coords[0],
            icon=folium.Icon(color="green", icon="play", prefix="fa"),
            tooltip="Start",
        ).add_to(m)
        folium.Marker(
            coords[-1],
            icon=folium.Icon(color="red", icon="flag", prefix="fa"),
            tooltip="Destination",
        ).add_to(m)

    folium.LayerControl(position="topright").add_to(m)
    return m
