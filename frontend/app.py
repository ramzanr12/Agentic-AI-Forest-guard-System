"""
Agentic AI Forest Guard — Streamlit Frontend
Green Glassmorphism theme | Real-time dashboard
"""
import streamlit as st
import time
from datetime import datetime, timezone

st.set_page_config(
    page_title="AI Forest Guard",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

from styles import MAIN_CSS, ALERT_SOUND_JS, risk_bar, glass_card, badge, weather_grid
from api_client import login, get_overview

st.markdown(MAIN_CSS, unsafe_allow_html=True)
st.markdown(ALERT_SOUND_JS, unsafe_allow_html=True)


def _init_state():
    defaults = {
        "token": None, "username": None, "role": None,
        "full_name": None, "page": "Overview",
        "dark_mode": True, "sound_enabled": True,
        "last_alert_count": 0, "chat_history": [],
        "route_path": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


# ── Login Page ─────────────────────────────────────────────────────────────
def render_login():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center;padding:3rem 0 2rem">
          <div style="font-size:4rem;margin-bottom:0.5rem;filter:drop-shadow(0 0 20px #22c55e88)">🌿</div>
          <h1 style="font-family:'Syne',sans-serif;font-size:2.4rem;
              background:linear-gradient(135deg,#22c55e,#4ade80);
              -webkit-background-clip:text;-webkit-text-fill-color:transparent;
              margin:0 0 0.3rem">AI Forest Guard</h1>
          <p style="color:#86c99a;font-size:0.92rem;margin:0">
              Smart Forest Intelligence System v2.0
          </p>
        </div>""", unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["🔑 Sign In", "📝 Register"])

        with tab1:
            username = st.text_input("Username", placeholder="admin / ranger_arjun / visitor_01")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            ca, cb = st.columns(2)
            with ca:
                if st.button("Sign In", use_container_width=True, type="primary"):
                    if username and password:
                        with st.spinner("Authenticating..."):
                            resp = login(username, password)
                        if resp:
                            st.session_state.token     = resp["access_token"]
                            st.session_state.username  = resp["username"]
                            st.session_state.role      = resp["role"]
                            st.session_state.full_name = resp.get("full_name", "")
                            st.success(f"Welcome, {resp.get('full_name', username)}!")
                            time.sleep(0.6); st.rerun()
                        else:
                            st.error("❌ Invalid credentials. Check backend is running.")
                    else:
                        st.warning("Enter username and password.")
            with cb:
                if st.button("Demo Login", use_container_width=True):
                    resp = login("admin", "admin123")
                    if resp:
                        st.session_state.token     = resp["access_token"]
                        st.session_state.username  = resp["username"]
                        st.session_state.role      = resp["role"]
                        st.session_state.full_name = resp.get("full_name", "Admin")
                        st.rerun()
                    else:
                        st.info("Backend not ready. Try `docker compose up`.")

            st.markdown("""
            <div style="margin-top:1.2rem;padding:0.9rem 1rem;
                background:rgba(34,197,94,0.06);border-radius:10px;
                border:1px solid rgba(34,197,94,0.14);font-size:0.81rem;color:#86c99a;line-height:1.8">
              <b style="color:#22c55e">Demo Accounts:</b><br>
              👑 admin / admin123 &nbsp;·&nbsp;
              👮 ranger_arjun / ranger123<br>
              🚶 visitor_01 / visitor123 &nbsp;·&nbsp;
              🤝 volunteer_01 / vol123
            </div>""", unsafe_allow_html=True)

        with tab2:
            r_name  = st.text_input("Full Name", key="r_name")
            r_user  = st.text_input("Username",  key="r_user")
            r_email = st.text_input("Email",     key="r_email")
            r_pass  = st.text_input("Password",  type="password", key="r_pass")
            r_role  = st.selectbox("Role", ["visitor","volunteer","ranger"])
            if st.button("Register", use_container_width=True, type="primary"):
                from api_client import register
                if all([r_name, r_user, r_email, r_pass]):
                    res = register(r_user, r_email, r_name, r_pass, r_role)
                    if res:
                        st.success("✅ Registered! Sign in now.")
                    else:
                        st.error("Registration failed (username or email may already exist).")
                else:
                    st.warning("Fill all fields.")


# ── Sidebar ────────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="padding:1.4rem 1.2rem 0.8rem;border-bottom:1px solid rgba(34,197,94,0.14)">
          <div style="display:flex;align-items:center;gap:12px">
            <div style="font-size:2rem;filter:drop-shadow(0 0 10px #22c55e88)">🌿</div>
            <div>
              <div style="font-family:'Syne',sans-serif;font-weight:800;
                  font-size:1rem;color:#22c55e;line-height:1.2">AI Forest Guard</div>
              <div style="font-size:0.68rem;color:#86c99a">Intelligence System v2.0</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

        role_icons = {"admin":"👑","ranger":"👮","visitor":"🚶","volunteer":"🤝"}
        ico = role_icons.get(st.session_state.role or "visitor", "👤")
        st.markdown(f"""
        <div style="margin:0.8rem 1rem 0;background:rgba(34,197,94,0.07);
          border:1px solid rgba(34,197,94,0.16);border-radius:10px;padding:10px 12px">
          <div style="font-weight:700;color:#22c55e;font-size:0.88rem">
            {ico} {st.session_state.full_name or st.session_state.username}</div>
          <div style="color:#86c99a;font-size:0.73rem;text-transform:capitalize;margin-top:1px">
            {st.session_state.role}</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:0.6rem'/>", unsafe_allow_html=True)

        pages = [
            ("🏠","Overview"), ("🗺️","Live Map"), ("🚨","Alerts"),
            ("👮","Ranger Ops"), ("🚶","Visitor System"), ("🤝","Volunteer Community"),
            ("🦁","Wildlife"), ("📊","Reports"), ("🤖","AI Assistant"),
        ]
        for icon, page in pages:
            active = st.session_state.page == page
            if st.button(f"{icon}  {page}", key=f"nav_{page}",
                         use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state.page = page
                st.rerun()

        st.markdown("<hr style='border-color:rgba(34,197,94,0.12);margin:0.8rem 0'/>",
                    unsafe_allow_html=True)

        overview = get_overview()
        if overview:
            fa = overview.get("active_alerts", 0)
            fr = overview.get("fire_risk", 0)
            ac = "#ef4444" if fa > 5 else "#f59e0b" if fa > 2 else "#22c55e"
            fc = "#ef4444" if fr > 70 else "#f59e0b" if fr > 40 else "#22c55e"
            st.markdown(f"""
            <div style="padding:0 0.2rem;font-size:0.8rem">
              <div style="font-size:0.65rem;color:#86c99a;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px">Live Status</div>
              <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid rgba(34,197,94,0.08)">
                <span style="color:#86c99a">🚨 Alerts</span>
                <span style="color:{ac};font-weight:700">{fa}</span>
              </div>
              <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid rgba(34,197,94,0.08)">
                <span style="color:#86c99a">👮 Rangers</span>
                <span style="color:#22c55e;font-weight:700">{overview.get('rangers_on_duty',0)}/{overview.get('total_rangers',0)}</span>
              </div>
              <div style="display:flex;justify-content:space-between;padding:5px 0">
                <span style="color:#86c99a">🔥 Fire Risk</span>
                <span style="color:{fc};font-weight:700">{fr:.0f}%</span>
              </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<hr style='border-color:rgba(34,197,94,0.12);margin:0.8rem 0'/>",
                    unsafe_allow_html=True)

        st.session_state.sound_enabled = st.toggle("🔊 Sound Alerts", value=st.session_state.sound_enabled)

        if st.button("🚪 Sign Out", use_container_width=True, type="secondary"):
            for k in ["token","username","role","full_name"]:
                st.session_state[k] = None
            st.session_state.page = "Overview"
            st.session_state.chat_history = []
            st.rerun()

        st.markdown("""
        <div style="margin-top:0.8rem;padding:0.8rem 0.4rem">
          <div style="font-size:0.65rem;color:#86c99a;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px">Emergency</div>
          <div style="display:flex;flex-direction:column;gap:5px;font-size:0.78rem">
            <div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.25);border-radius:8px;padding:5px 10px;display:flex;justify-content:space-between">
              <span>🚔 Police</span><b style="color:#f87171">100</b></div>
            <div style="background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.25);border-radius:8px;padding:5px 10px;display:flex;justify-content:space-between">
              <span>🔥 Fire Dept</span><b style="color:#fbbf24">101</b></div>
            <div style="background:rgba(59,130,246,0.1);border:1px solid rgba(59,130,246,0.25);border-radius:8px;padding:5px 10px;display:flex;justify-content:space-between">
              <span>🚑 Ambulance</span><b style="color:#60a5fa">108</b></div>
          </div>
        </div>""", unsafe_allow_html=True)


# ── Page: Overview ─────────────────────────────────────────────────────────
def page_overview():
    from api_client import get_weather, get_risk_scores, get_news, get_alerts

    now_str = datetime.now(timezone.utc).strftime("%d %b %Y · %H:%M UTC")
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1.5rem">
      <div>
        <h1 style="margin:0;font-size:1.8rem;letter-spacing:-0.02em">🌿 Forest Intelligence Overview</h1>
        <p style="color:#86c99a;margin:3px 0 0;font-size:0.88rem">Real-time monitoring dashboard</p>
      </div>
      <div style="font-size:0.78rem;color:#86c99a;background:rgba(34,197,94,0.07);
          border:1px solid rgba(34,197,94,0.14);border-radius:8px;padding:6px 12px">
        🕐 {now_str}
      </div>
    </div>""", unsafe_allow_html=True)

    overview = get_overview()
    if not overview:
        st.error("⚠️ Backend unavailable. Start with `docker compose up --build`")
        return

    # KPI Row
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    kpis = [
        (c1,"🚨","Active Alerts",  overview.get("active_alerts",0),    f"{overview.get('critical_alerts',0)} critical","inverse"),
        (c2,"👮","Rangers on Duty",overview.get("rangers_on_duty",0),   f"/{overview.get('total_rangers',0)} total","normal"),
        (c3,"🚶","Visitors Inside",overview.get("visitors_inside",0),   "in forest","normal"),
        (c4,"🔥","Fire Risk",      f"{overview.get('fire_risk',0):.0f}%","current","inverse"),
        (c5,"🎯","Poaching Risk",  f"{overview.get('poaching_risk',0):.0f}%","current","inverse"),
        (c6,"🦁","Species Count",  overview.get("species_count",7),     "tracked","normal"),
    ]
    for col,icon,label,val,delta,dc in kpis:
        with col:
            st.metric(f"{icon} {label}", val, delta=delta, delta_color=dc)

    st.markdown("<div style='margin:1rem 0'/>", unsafe_allow_html=True)

    # Risk + Weather — FIXED: weather_grid() builds pure HTML, no nested f-string
    col_l, col_r = st.columns([1.2, 1])

    with col_l:
        scores = get_risk_scores()
        risk_html = (
            '<div style="font-family:Syne,sans-serif;font-size:1rem;color:#22c55e;font-weight:700;margin-bottom:1rem">⚡ Threat Risk Scores</div>'
            + risk_bar("🔥 Fire Risk",      scores.get("fire",      25))
            + risk_bar("🎯 Poaching Risk",  scores.get("poaching",  20))
            + risk_bar("🚨 Intrusion Risk", scores.get("intrusion", 15))
        )
        st.markdown(glass_card(risk_html), unsafe_allow_html=True)

    with col_r:
        w = get_weather()
        if w:
            fire_risk_val = float(w.get("fire_risk", overview.get("fire_risk_weather", 25)))
            # weather_grid returns a plain HTML string — safe to wrap directly
            st.markdown(glass_card(weather_grid(w, fire_risk_val)), unsafe_allow_html=True)

    # Recent Alerts
    st.markdown("<div style='margin:0.5rem 0'/>", unsafe_allow_html=True)
    alerts = get_alerts(status="active")
    if alerts:
        st.markdown("### 🚨 Recent Active Alerts")
        for a in alerts[:6]:
            sev = a.get("severity","medium")
            ahtml = (
                f"<div style='display:flex;justify-content:space-between;align-items:flex-start;gap:8px'>"
                f"  <div style='flex:1'>"
                f"    <div style='margin-bottom:5px'>"
                f"      <span class='badge badge-{sev}'>{sev}</span>&nbsp;"
                f"      <b style='color:#e2fce8'>{a.get('alert_type','').replace('_',' ').title()}</b>"
                f"      <span style='color:#86c99a;font-size:0.8rem'> — {a.get('zone','?')}</span>"
                f"    </div>"
                f"    <div style='color:#86c99a;font-size:0.83rem'>{a.get('description','')[:120]}</div>"
                f"  </div>"
                f"  <div style='color:#4a5568;font-size:0.73rem;white-space:nowrap'>{a.get('created_at','')[:16]}</div>"
                f"</div>"
            )
            st.markdown(glass_card(ahtml, flash=(sev=="critical")), unsafe_allow_html=True)

        critical_count = sum(1 for a in alerts if a.get("severity")=="critical")
        if critical_count > 0 and st.session_state.sound_enabled:
            st.markdown(f"<script>setTimeout(()=>checkAlerts({len(alerts)},'critical'),500);</script>",
                        unsafe_allow_html=True)

    # News
    st.markdown("<div style='margin:0.5rem 0'/>", unsafe_allow_html=True)
    news = get_news()
    if news:
        st.markdown("### 📰 Forest & Wildlife News")
        cols = st.columns(2)
        for i, art in enumerate(news[:4]):
            with cols[i % 2]:
                nhtml = (
                    f"<div style='font-size:0.88rem;font-weight:600;color:#e2fce8;margin-bottom:5px'>{art.get('title','')[:88]}</div>"
                    f"<div style='display:flex;justify-content:space-between;font-size:0.73rem;color:#86c99a'>"
                    f"  <span>📰 {art.get('source','')}</span>"
                    f"  <span>{art.get('publishedAt','')}</span>"
                    f"</div>"
                )
                st.markdown(glass_card(nhtml), unsafe_allow_html=True)


# ── Page: Live Map ─────────────────────────────────────────────────────────
def page_live_map():
    from streamlit_folium import st_folium
    from map_utils import build_forest_map
    from api_client import get_map_data, get_route

    st.markdown("## 🗺️ Live Forest Map")
    col_ctrl, col_map = st.columns([1, 3.5])

    with col_ctrl:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("**🎛️ Map Layers**")
        show_rangers  = st.checkbox("👮 Rangers",   value=True)
        show_alerts   = st.checkbox("🚨 Alerts",    value=True)
        show_wildlife = st.checkbox("🦁 Wildlife",  value=True)
        show_zones    = st.checkbox("🗺️ Zones",     value=True)
        show_heatmap  = st.checkbox("🌡️ Heat Map",  value=False)
        st.markdown("---")
        st.markdown("**🔍 A* Route Finder**")
        from_lat = st.number_input("From Lat", value=11.47, format="%.4f", step=0.001)
        from_lon = st.number_input("From Lon", value=76.91, format="%.4f", step=0.001)
        to_lat   = st.number_input("To Lat",   value=11.53, format="%.4f", step=0.001)
        to_lon   = st.number_input("To Lon",   value=76.97, format="%.4f", step=0.001)
        if st.button("🔍 Find Route", use_container_width=True):
            with st.spinner("Computing A* path..."):
                result = get_route(from_lat, from_lon, to_lat, to_lon)
            if result and result.get("success"):
                st.session_state.route_path = result["path"]
                st.success(f"✅ {result['distance_km']} km | ~{result['estimated_minutes']} min")
            else:
                st.error("No path found.")
                st.session_state.route_path = None
        if st.button("❌ Clear Route", use_container_width=True):
            st.session_state.route_path = None
        st.markdown("</div>", unsafe_allow_html=True)

    with col_map:
        map_data  = get_map_data()
        rangers   = map_data.get("rangers",  []) if show_rangers  else []
        alerts    = map_data.get("alerts",   []) if show_alerts   else []
        sightings = map_data.get("sightings",[]) if show_wildlife else []
        zones     = map_data.get("zones",    []) if show_zones    else []
        route     = st.session_state.get("route_path", [])
        fmap = build_forest_map(rangers=rangers, alerts=alerts,
                                sightings=sightings, zones=zones,
                                route=route, show_heatmap=show_heatmap)
        st_folium(fmap, width=None, height=620, returned_objects=[])


# ── Page: Alerts ───────────────────────────────────────────────────────────
def page_alerts():
    from api_client import get_alerts, get_alert_stats, ack_alert, resolve_alert, create_alert

    st.markdown("## 🚨 Alert Management")
    stats = get_alert_stats()
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("📋 Total",    stats.get("total",0))
    with c2: st.metric("🔴 Active",   stats.get("active",0),   delta_color="inverse")
    with c3: st.metric("⚡ Critical", stats.get("critical",0), delta_color="inverse")
    with c4: st.metric("✅ Resolved", stats.get("resolved",0), delta_color="normal")

    st.markdown("<div style='margin:0.8rem 0'/>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["🔴 Active Alerts", "✅ Resolved", "➕ Create Alert"])

    with tab1:
        f1, f2 = st.columns(2)
        with f1: sev_filter  = st.selectbox("Filter Severity", ["All","critical","high","medium","low"])
        with f2: type_filter = st.text_input("Filter Type", placeholder="fire, poaching...")
        alerts = get_alerts(status="active")
        if sev_filter != "All":  alerts = [a for a in alerts if a.get("severity") == sev_filter]
        if type_filter:          alerts = [a for a in alerts if type_filter.lower() in a.get("alert_type","")]
        if not alerts:
            st.markdown(glass_card("✅ <span style='color:#22c55e'>No active alerts matching filters.</span>"),
                        unsafe_allow_html=True)
        else:
            for a in alerts:
                sev = a.get("severity","medium")
                ahtml = (
                    f"<div style='display:flex;justify-content:space-between;align-items:flex-start;gap:12px'>"
                    f"  <div style='flex:1'>"
                    f"    <div style='display:flex;align-items:center;gap:8px;margin-bottom:6px'>"
                    f"      <span class='badge badge-{sev}'>{sev}</span>"
                    f"      <b style='color:#e2fce8'>{a.get('alert_type','').replace('_',' ').title()}</b>"
                    f"    </div>"
                    f"    <div style='font-size:0.84rem;color:#86c99a'>{a.get('description','')[:150]}</div>"
                    f"    <div style='font-size:0.73rem;color:#4a5568;margin-top:5px'>"
                    f"      📍 {a.get('zone','?')} &nbsp;·&nbsp; 🎯 {a.get('confidence',0)*100:.0f}% &nbsp;·&nbsp; 🕐 {a.get('created_at','')[:16]}"
                    f"    </div>"
                    f"  </div>"
                    f"</div>"
                )
                st.markdown(glass_card(ahtml, flash=(sev=="critical")), unsafe_allow_html=True)
                b1, b2, _ = st.columns([1,1,4])
                with b1:
                    if st.button("✓ Ack", key=f"ack_{a['id']}", use_container_width=True):
                        ack_alert(a["id"]); st.rerun()
                with b2:
                    if st.button("✓ Resolve", key=f"res_{a['id']}", use_container_width=True):
                        resolve_alert(a["id"]); st.rerun()

    with tab2:
        resolved = get_alerts(status="resolved")
        if not resolved:
            st.info("No resolved alerts yet.")
        else:
            import pandas as pd
            df = pd.DataFrame([{
                "ID":a["id"],"Type":a["alert_type"],"Severity":a["severity"],
                "Zone":a["zone"],"Created":a["created_at"][:16]
            } for a in resolved[:30]])
            st.dataframe(df, use_container_width=True, hide_index=True)

    with tab3:
        c1, c2 = st.columns(2)
        with c1:
            n_type = st.selectbox("Alert Type", ["fire","poaching","intrusion","vehicle","geofence_violation","other"])
            n_sev  = st.selectbox("Severity",   ["medium","high","critical","low"])
            n_zone = st.text_input("Zone", "Zone-A")
        with c2:
            n_lat  = st.number_input("Latitude",   value=11.4916, format="%.4f")
            n_lon  = st.number_input("Longitude",  value=76.9294, format="%.4f")
            n_conf = st.slider("Confidence", 0.0, 1.0, 0.85, 0.05)
        n_desc = st.text_area("Description", placeholder="Describe the incident...")
        if st.button("📢 Create Alert", use_container_width=True, type="primary"):
            if create_alert({"alert_type":n_type,"severity":n_sev,"lat":n_lat,
                             "lon":n_lon,"zone":n_zone,"description":n_desc,"confidence":n_conf}):
                st.success("✅ Alert created!"); st.rerun()
            else:
                st.error("Failed to create alert.")


# ── Page: Ranger Ops ───────────────────────────────────────────────────────
def page_ranger_ops():
    from api_client import get_rangers, get_alerts, dispatch_ranger, get_patrol_route
    from streamlit_folium import st_folium
    from map_utils import build_forest_map

    st.markdown("## 👮 Ranger Operations")
    rangers   = get_rangers()
    on_duty   = [r for r in rangers if r.get("is_on_duty")]
    off_duty  = [r for r in rangers if not r.get("is_on_duty")]

    c1,c2,c3 = st.columns(3)
    with c1: st.metric("👮 Total Rangers", len(rangers))
    with c2: st.metric("🟢 On Duty",       len(on_duty))
    with c3: st.metric("⚫ Off Duty",      len(off_duty))

    tab1, tab2, tab3 = st.tabs(["👮 Ranger Status","🚀 Dispatch","🗺️ Patrol Routes"])

    with tab1:
        st.markdown("<div style='margin:0.4rem 0'/>", unsafe_allow_html=True)
        for r in rangers:
            duty   = r.get("is_on_duty", False)
            status = r.get("status","off_duty")
            dot    = "🟢" if duty else "⚫"
            rhtml = (
                f"<div style='display:flex;align-items:center;justify-content:space-between'>"
                f"  <div>"
                f"    <div style='display:flex;align-items:center;gap:8px;margin-bottom:3px'>"
                f"      {dot} <b style='color:#e2fce8'>{r.get('name','?')}</b>"
                f"      <span style='color:#86c99a;font-size:0.78rem'>#{r.get('badge','?')}</span>"
                f"      <span class='badge badge-{'low' if duty else 'medium'}'>{status}</span>"
                f"    </div>"
                f"    <div style='font-size:0.78rem;color:#86c99a'>"
                f"      📍 {r.get('sector','?')} &nbsp;·&nbsp; 🌐 {r.get('lat',0):.4f}, {r.get('lon',0):.4f}"
                f"    </div>"
                f"  </div>"
                f"  <div style='font-size:0.78rem;color:#86c99a'>📞 {r.get('phone','')}</div>"
                f"</div>"
            )
            st.markdown(glass_card(rhtml), unsafe_allow_html=True)

    with tab2:
        alerts = get_alerts(status="active")
        if not on_duty or not alerts:
            st.info("No rangers on duty or no active alerts.")
        else:
            c1,c2,c3 = st.columns(3)
            with c1:
                r_opts = {f"{r.get('badge')} — {r.get('name')} ({r.get('sector')})":r for r in on_duty}
                sel_r  = st.selectbox("Select Ranger", list(r_opts.keys()))
            with c2:
                a_opts = {f"[{a.get('severity','?').upper()}] {a.get('alert_type','')} @ {a.get('zone','')}":a for a in alerts[:15]}
                sel_a  = st.selectbox("Select Alert",  list(a_opts.keys()))
            with c3:
                st.markdown("<div style='margin-top:1.7rem'/>", unsafe_allow_html=True)
                if st.button("🚀 Dispatch", use_container_width=True, type="primary"):
                    ranger = r_opts[sel_r]; alert = a_opts[sel_a]
                    res = dispatch_ranger(ranger["badge"], alert.get("lat",11.4916),
                                         alert.get("lon",76.9294), alert.get("id"))
                    if res:
                        st.success(f"✅ {ranger.get('name')} dispatched!"); st.rerun()
                    else:
                        st.error("Dispatch failed.")

    with tab3:
        badges = [r.get("badge","") for r in on_duty]
        if badges:
            sel_badge  = st.selectbox("Select Ranger Badge", badges)
            route_data = get_patrol_route(sel_badge)
            if route_data and route_data.get("route"):
                pts = route_data["route"]
                fmap = build_forest_map(rangers=on_duty, route=pts,
                                        center_lat=pts[0]["lat"], center_lon=pts[0]["lon"], zoom=13)
                st_folium(fmap, width=None, height=450, returned_objects=[])
                st.success(f"Patrol route for {sel_badge} — {route_data.get('sector','?')}")


# ── Page: Visitor System ───────────────────────────────────────────────────
def page_visitor_system():
    from api_client import get_visitors, get_visitor_stats, log_entry, log_exit, get_visitor_qr
    import base64

    st.markdown("## 🚶 Visitor Management")
    stats = get_visitor_stats()
    c1,c2,c3 = st.columns(3)
    with c1: st.metric("📋 Registered",     stats.get("total_registered",0))
    with c2: st.metric("🟢 Inside Now",      stats.get("currently_inside",0))
    with c3: st.metric("⏰ Overstay Alerts", stats.get("overstay_alerts",0), delta_color="inverse")

    tab1, tab2, tab3 = st.tabs(["📋 Visitor List","🎫 QR Ticket","📊 Activity Log"])

    with tab1:
        if st.session_state.role not in ("admin","ranger"):
            st.warning("⚠️ Visitor list visible to Admin and Rangers only.")
        else:
            visitors = get_visitors()
            if not visitors:
                st.info("No visitors registered.")
            else:
                for v in visitors:
                    inside = v.get("is_inside", False)
                    status = "🟢 Inside" if inside else "⚫ Outside"
                    vhtml = (
                        f"<div style='display:flex;justify-content:space-between;align-items:center'>"
                        f"  <div>"
                        f"    <b style='color:#e2fce8'>{v.get('full_name','?')}</b>"
                        f"    <span style='color:#86c99a;font-size:0.8rem;margin-left:6px'>@{v.get('username','')}</span>"
                        f"    <div style='font-size:0.78rem;color:#86c99a;margin-top:3px'>"
                        f"      🎫 {v.get('permit_type','').replace('_',' ').title()} &nbsp;·&nbsp;"
                        f"      🚗 {v.get('vehicle','-')} &nbsp;·&nbsp; 👥 {v.get('group_size',1)}"
                        f"    </div>"
                        f"  </div>"
                        f"  <div style='text-align:right;font-size:0.82rem'>"
                        f"    <div>{status}</div>"
                        f"    <div style='font-size:0.72rem;color:#4a5568'>{v.get('entry_time','')[:16] if v.get('entry_time') else 'Not entered'}</div>"
                        f"  </div>"
                        f"</div>"
                    )
                    st.markdown(glass_card(vhtml), unsafe_allow_html=True)
                    b1,b2,_ = st.columns([1,1,4])
                    with b1:
                        if st.button("✅ Entry", key=f"ent_{v['id']}", use_container_width=True):
                            if log_entry(v["id"]): st.success("Entry logged!"); st.rerun()
                    with b2:
                        if st.button("🚪 Exit",  key=f"ext_{v['id']}", use_container_width=True):
                            log_exit(v["id"]); st.rerun()

    with tab2:
        st.markdown("**Generate Visitor QR Ticket**")
        if st.session_state.role not in ("admin","ranger"):
            vid = st.number_input("Your Visitor ID", min_value=1, value=1, step=1)
        else:
            visitors = get_visitors()
            v_names  = {f"{v.get('full_name','?')} (ID:{v['id']})": v["id"] for v in visitors} if visitors else {}
            sel  = st.selectbox("Select Visitor", list(v_names.keys()) if v_names else ["None"])
            vid  = v_names.get(sel, 1)
        if st.button("🎫 Generate QR", use_container_width=True, type="primary"):
            with st.spinner("Generating..."):
                qr_b64 = get_visitor_qr(vid)
            if qr_b64:
                from PIL import Image; import io
                img = Image.open(io.BytesIO(base64.b64decode(qr_b64)))
                col_q, _ = st.columns([1,2])
                with col_q: st.image(img, caption=f"Visitor Ticket — ID {vid}", width=220)
                st.success("✅ QR Ticket generated!")
            else:
                st.error("Could not generate QR.")

    with tab3:
        if st.session_state.role in ("admin","ranger"):
            visitors = get_visitors()
            if visitors:
                import pandas as pd
                rows = [{"Visitor":v.get("full_name","?"),"Status":"Inside" if v.get("is_inside") else "Outside",
                         "Entry":v.get("entry_time","")[:16] if v.get("entry_time") else "—",
                         "Permit":v.get("permit_type",""),"Group":v.get("group_size",1)}
                        for v in visitors]
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("Activity log visible to Admin and Rangers.")


# ── Page: Volunteer Community ──────────────────────────────────────────────
def page_volunteer():
    from api_client import get_leaderboard, get_vol_reports, submit_vol_report

    st.markdown("## 🤝 Volunteer Community")
    tab1, tab2, tab3 = st.tabs(["🏆 Leaderboard","📋 Community Feed","📝 Submit Report"])

    with tab1:
        leaderboard = get_leaderboard()
        if not leaderboard:
            st.info("No volunteers yet.")
        else:
            medals = ["🥇","🥈","🥉"] + ["🏅"]*20
            for i, v in enumerate(leaderboard[:10]):
                verified_badge = "<span class='badge badge-low' style='margin-left:6px'>✓ Verified</span>" if v.get('verified') else ""
                vhtml = (
                    f"<div style='display:flex;align-items:center;gap:14px'>"
                    f"  <div style='font-size:1.5rem'>{medals[i]}</div>"
                    f"  <div style='flex:1'>"
                    f"    <b style='color:#e2fce8'>{v.get('full_name','Volunteer')}</b>"
                    f"    {verified_badge}"
                    f"    <div style='font-size:0.78rem;color:#86c99a'>Zone: {v.get('zone','?')}</div>"
                    f"  </div>"
                    f"  <div style='text-align:right'>"
                    f"    <div style='font-size:1.4rem;font-weight:700;color:#4ade80;font-family:Syne,sans-serif'>{v.get('points',0)}</div>"
                    f"    <div style='font-size:0.7rem;color:#86c99a'>points</div>"
                    f"  </div>"
                    f"</div>"
                )
                st.markdown(glass_card(vhtml), unsafe_allow_html=True)

    with tab2:
        reports = get_vol_reports()
        if not reports:
            st.info("No community reports yet. Be the first to report!")
        else:
            for rep in reports[:20]:
                sc = {"approved":"#22c55e","pending":"#f59e0b","rejected":"#ef4444"}.get(rep.get("status","pending"),"#86c99a")
                pts_str = f"&nbsp;&#183;&nbsp; <b style='color:#4ade80'>+{rep.get('points',0)} pts</b>" if rep.get("points") else ""
                rhtml = (
                    f"<div style='display:flex;justify-content:space-between;margin-bottom:6px'>"
                    f"  <span class='badge badge-medium'>{rep.get('incident_type','?')}</span>"
                    f"  <span style='color:{sc};font-size:0.78rem'>&#9679; {rep.get('status','?').title()}</span>"
                    f"  <span style='font-size:0.72rem;color:#4a5568'>{rep.get('created_at','')[:16]}</span>"
                    f"</div>"
                    f"<div style='color:#e2fce8;font-size:0.86rem'>{rep.get('description','')[:200]}</div>"
                    f"<div style='font-size:0.76rem;color:#86c99a;margin-top:5px'>"
                    f"  &#128205; {rep.get('lat',0):.4f}, {rep.get('lon',0):.4f} {pts_str}"
                    f"</div>"
                )
                st.markdown(glass_card(rhtml), unsafe_allow_html=True)

    with tab3:
        if not st.session_state.token:
            st.warning("Sign in to submit a report.")
        else:
            c1,c2 = st.columns(2)
            with c1:
                inc_type = st.selectbox("Incident Type",["fire","poaching","animal_sighting","trail_damage","illegal_dumping","other"])
                r_lat    = st.number_input("Latitude",  value=11.4916, format="%.4f")
            with c2:
                r_lon    = st.number_input("Longitude", value=76.9294, format="%.4f")
            r_desc = st.text_area("Description (min 20 chars)", placeholder="Describe what you observed...")
            pts_map = {"fire":20,"poaching":25,"animal_sighting":10,"trail_damage":8,"illegal_dumping":12,"other":5}
            st.markdown(f"<div style='color:#4ade80;font-size:0.84rem'>🏅 Points for this report: <b>+{pts_map.get(inc_type,5)}</b></div>",
                        unsafe_allow_html=True)
            if st.button("📤 Submit Report", use_container_width=True, type="primary"):
                if len(r_desc.strip()) < 20:
                    st.warning("Description too short (min 20 chars).")
                elif st.session_state.role != "volunteer":
                    st.warning("Only volunteers can submit community reports.")
                else:
                    res = submit_vol_report(inc_type, r_desc, r_lat, r_lon)
                    if res:
                        st.success(f"✅ Submitted! You earned +{pts_map.get(inc_type,5)} points.")
                        st.rerun()
                    else:
                        st.error("Submission failed.")


# ── Page: Wildlife ─────────────────────────────────────────────────────────
def page_wildlife():
    from api_client import get_population, get_sightings
    from streamlit_folium import st_folium
    from map_utils import build_forest_map

    st.markdown("## 🦁 Wildlife Intelligence")
    tab1, tab2, tab3 = st.tabs(["📊 Population","🐾 Sightings","🗺️ Heatmap"])

    with tab1:
        pop = get_population()
        if pop:
            cols = st.columns(3)
            sp_colors = {"elephant":"#f59e0b","tiger":"#ef4444","deer":"#22c55e",
                         "leopard":"#a78bfa","bear":"#8b5cf6","peacock":"#06b6d4","crocodile":"#84cc16"}
            for i,(sp,data) in enumerate(pop.items()):
                with cols[i%3]:
                    trend  = data.get("trend","stable")
                    arr    = "↑" if trend=="increasing" else "↓" if trend=="decreasing" else "→"
                    tc     = "#22c55e" if trend=="increasing" else "#ef4444" if trend=="decreasing" else "#f59e0b"
                    sc     = sp_colors.get(sp,"#22c55e")
                    phtml  = (
                        f"<div style='text-align:center;padding:0.5rem'>"
                        f"  <div style='font-size:1.8rem'>{data.get('icon','🐾')}</div>"
                        f"  <div style='font-weight:700;color:#e2fce8;font-family:Syne,sans-serif;font-size:0.95rem;text-transform:capitalize;margin:4px 0'>{sp}</div>"
                        f"  <div style='font-size:2rem;font-weight:800;color:{sc};font-family:Syne,sans-serif;line-height:1'>{data.get('count','?')}</div>"
                        f"  <div style='font-size:0.7rem;color:#86c99a'>individuals</div>"
                        f"  <div style='margin-top:5px;font-size:0.8rem;color:{tc}'>{arr} {trend.title()}</div>"
                        f"  <div style='font-size:0.75rem;color:#4ade80'>+{data.get('today_sightings',0)} today</div>"
                        f"</div>"
                    )
                    st.markdown(glass_card(phtml), unsafe_allow_html=True)

    with tab2:
        c1, _ = st.columns([1,3])
        with c1: species_filter = st.selectbox("Species",["All","elephant","tiger","deer","leopard","bear"])
        sightings = get_sightings(species=None if species_filter=="All" else species_filter)
        if sightings:
            import pandas as pd
            df = pd.DataFrame([{
                "Animal ID": s.get("animal_id",""), "Species": s.get("species","").title(),
                "Zone": s.get("zone",""), "Confidence": f"{s.get('confidence',0)*100:.0f}%",
                "Seen At": s.get("seen_at","")[:16]
            } for s in sightings[:50]])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No sightings recorded yet.")

    with tab3:
        sightings_all = get_sightings()
        fmap = build_forest_map(sightings=sightings_all, show_heatmap=True)
        st_folium(fmap, width=None, height=500, returned_objects=[])


# ── Page: Reports ──────────────────────────────────────────────────────────
def page_reports():
    from api_client import get_reports, get_daily_summary, get_weekly_summary, \
        generate_daily_report, generate_weekly_report

    st.markdown("## 📊 Reports & Intelligence Summaries")
    tab1, tab2, tab3, tab4 = st.tabs(["📅 Daily","📆 Weekly","📄 Archive","⚙️ Generate"])

    with tab1:
        with st.spinner("Loading..."):
            summary = get_daily_summary()
        if summary: st.markdown(summary)
        else:       st.info("Daily summary not yet available.")

    with tab2:
        with st.spinner("Loading..."):
            weekly = get_weekly_summary()
        if weekly: st.markdown(weekly)
        else:      st.info("Weekly report not yet available.")

    with tab3:
        reports = get_reports()
        if not reports:
            st.info("No reports generated yet.")
        else:
            import pandas as pd
            df = pd.DataFrame([{
                "Date":r.get("report_date",""),"Alerts":r.get("total_alerts",0),
                "Critical":r.get("critical_alerts",0),"Visitors":r.get("visitors_today",0),
                "Sightings":r.get("animal_sightings",0),"Rangers":r.get("rangers_on_duty",0),
            } for r in reports])
            st.dataframe(df, use_container_width=True, hide_index=True)
            for r in reports[:5]:
                st.markdown(glass_card(f"<b style='color:#22c55e'>{r.get('report_date','')}</b> — {r.get('summary','')[:200]}"),
                            unsafe_allow_html=True)

    with tab4:
        if st.session_state.role not in ("admin","ranger"):
            st.warning("⚠️ Requires Admin or Ranger access.")
        else:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**📅 Daily Report**")
                date_input = st.date_input("Report Date")
                if st.button("📄 Generate Daily", use_container_width=True, type="primary"):
                    with st.spinner("Generating..."):
                        res = generate_daily_report(str(date_input))
                    if res: st.success(f"✅ Daily report: {res.get('date','')}")
                    else:   st.error("Generation failed.")
            with c2:
                st.markdown("**📆 Weekly Report**")
                st.markdown("<div style='height:2.1rem'/>", unsafe_allow_html=True)
                if st.button("📆 Generate Weekly", use_container_width=True, type="primary"):
                    with st.spinner("Generating..."):
                        res = generate_weekly_report()
                    if res: st.success(f"✅ Weekly report: {res.get('week','')}")
                    else:   st.error("Generation failed.")


# ── Page: AI Assistant ─────────────────────────────────────────────────────
def page_ai_assistant():
    from api_client import ai_chat

    st.markdown("## 🤖 AI Forest Intelligence Assistant")
    col1, col2 = st.columns([2.2, 1])

    with col1:
        if not st.session_state.chat_history:
            st.markdown(glass_card(
                "👋 <b style='color:#22c55e'>Forest AI</b>: Hello! I'm your AI Forest Intelligence assistant. "
                "Ask me about fire risk, wildlife, rangers, alerts, weather, or forest management."
            ), unsafe_allow_html=True)
        for msg in st.session_state.chat_history[-14:]:
            if msg["role"] == "user":
                st.markdown(
                    f"<div style='text-align:right;margin:6px 0'>"
                    f"<span style='background:rgba(34,197,94,0.15);border:1px solid rgba(34,197,94,0.25);"
                    f"border-radius:14px 14px 3px 14px;padding:8px 14px;display:inline-block;"
                    f"max-width:80%;color:#e2fce8;font-size:0.87rem'>{msg['text']}</span></div>",
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    f"<div style='margin:6px 0'>"
                    f"<span style='background:rgba(10,26,14,0.8);border:1px solid rgba(34,197,94,0.14);"
                    f"border-radius:3px 14px 14px 14px;padding:8px 14px;display:inline-block;"
                    f"max-width:85%;color:#e2fce8;font-size:0.87rem'>"
                    f"🤖 <b style='color:#22c55e'>Forest AI</b><br>{msg['text']}</span></div>",
                    unsafe_allow_html=True)

        ci, cs = st.columns([5,1])
        with ci:
            user_input = st.text_input("Message", key="chat_input", label_visibility="collapsed",
                                       placeholder="Ask about fire risk, wildlife, rangers...")
        with cs:
            send = st.button("Send", use_container_width=True, type="primary")
        if send and user_input.strip():
            st.session_state.chat_history.append({"role":"user","text":user_input})
            with st.spinner("Thinking..."):
                resp = ai_chat(user_input)
            st.session_state.chat_history.append({"role":"ai","text":resp})
            st.rerun()
        if st.button("🗑️ Clear Chat", type="secondary"):
            st.session_state.chat_history = []; st.rerun()

    with col2:
        st.markdown(glass_card(
            "<div style='font-weight:700;color:#22c55e;margin-bottom:10px;font-family:Syne,sans-serif'>💡 Quick Questions</div>"
        ), unsafe_allow_html=True)
        quick = [
            "What is the current fire risk?",
            "How many rangers are on duty?",
            "Tell me about tiger habitats",
            "What are active alerts?",
            "What's the weather today?",
            "Explain poaching prevention",
            "Show wildlife population",
            "What visitor permits exist?",
        ]
        for q in quick:
            if st.button(q, use_container_width=True, type="secondary", key=f"q_{q[:18]}"):
                st.session_state.chat_history.append({"role":"user","text":q})
                resp = ai_chat(q)
                st.session_state.chat_history.append({"role":"ai","text":resp})
                st.rerun()


# ── Main Router ────────────────────────────────────────────────────────────
def main():
    if not st.session_state.token:
        render_login()
        return

    render_sidebar()
    page = st.session_state.page

    if   page == "Overview":            page_overview()
    elif page == "Live Map":            page_live_map()
    elif page == "Alerts":              page_alerts()
    elif page == "Ranger Ops":          page_ranger_ops()
    elif page == "Visitor System":      page_visitor_system()
    elif page == "Volunteer Community": page_volunteer()
    elif page == "Wildlife":            page_wildlife()
    elif page == "Reports":             page_reports()
    elif page == "AI Assistant":        page_ai_assistant()
    else:
        st.info(f"Page '{page}' loading...")

    if page == "Overview":
        st.markdown("<script>setTimeout(()=>window.location.reload(),30000);</script>",
                    unsafe_allow_html=True)


if __name__ == "__main__":
    main()
