"""Green glassmorphism CSS for the Forest Guard dashboard."""

MAIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Inter:wght@300;400;500;600&display=swap');

:root {
  --g1: #030d06; --g2: #071510; --g3: #0d2416;
  --accent: #22c55e; --accent2: #16a34a; --accent3: #4ade80;
  --warn: #f59e0b; --danger: #ef4444; --info: #3b82f6;
  --glass: rgba(10,26,14,0.72); --glass2: rgba(34,197,94,0.07);
  --border: rgba(34,197,94,0.16); --text: #e2fce8; --text2: #86c99a;
  --radius: 14px; --shadow: 0 4px 24px rgba(0,0,0,0.5);
}

html, body, [data-testid="stAppViewContainer"] {
  background: radial-gradient(ellipse at 20% 20%, #071a0e 0%, #030d06 60%, #040f07 100%) !important;
  font-family: 'Inter', sans-serif !important;
  color: var(--text) !important; min-height: 100vh;
}
[data-testid="stSidebar"] {
  background: rgba(3,13,6,0.97) !important;
  border-right: 1px solid var(--border) !important;
  backdrop-filter: blur(24px) !important;
}
[data-testid="stSidebarContent"] { padding: 0 !important; }
[data-testid="stHeader"] { background: transparent !important; }

h1,h2,h3,h4,h5 { font-family: 'Syne', sans-serif !important; color: var(--accent) !important; }
.stMarkdown p { color: var(--text2) !important; }

[data-testid="metric-container"] {
  background: var(--glass) !important; border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important; backdrop-filter: blur(16px) !important;
  box-shadow: var(--shadow) !important; padding: 1rem 1.25rem !important;
  transition: all 0.25s ease !important;
}
[data-testid="metric-container"]:hover {
  transform: translateY(-3px) !important; border-color: rgba(34,197,94,0.4) !important;
  box-shadow: 0 8px 32px rgba(34,197,94,0.12) !important;
}
[data-testid="stMetricValue"]  { color: var(--accent3) !important; font-size: 1.9rem !important; font-family: 'Syne', sans-serif !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"]  { color: var(--text2) !important; font-size: 0.72rem !important; text-transform: uppercase; letter-spacing: 0.1em; }
[data-testid="stMetricDelta"]  { font-size: 0.8rem !important; }

.stButton > button {
  background: linear-gradient(135deg, var(--accent2) 0%, var(--accent) 100%) !important;
  color: #fff !important; border: none !important; border-radius: 10px !important;
  font-family: 'Syne', sans-serif !important; font-weight: 600 !important;
  letter-spacing: 0.04em !important; transition: all 0.2s ease !important;
  box-shadow: 0 2px 12px rgba(34,197,94,0.25) !important;
}
.stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 6px 22px rgba(34,197,94,0.45) !important; }
.stButton > button[kind="secondary"] {
  background: var(--glass) !important; border: 1px solid var(--border) !important;
  color: var(--accent) !important; box-shadow: none !important;
}
.stButton > button[kind="secondary"]:hover { background: rgba(34,197,94,0.1) !important; border-color: rgba(34,197,94,0.4) !important; }

.stTextInput > div > div > input, .stTextArea > div > div > textarea,
.stSelectbox > div > div, .stNumberInput > div > div > input {
  background: rgba(7,21,10,0.8) !important; border: 1px solid var(--border) !important;
  border-radius: 10px !important; color: var(--text) !important;
}

.stTabs [data-baseweb="tab-list"] {
  background: rgba(7,21,10,0.6) !important; border-radius: 12px !important;
  padding: 4px !important; border: 1px solid var(--border) !important; gap: 3px !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important; color: var(--text2) !important; border-radius: 9px !important;
  font-family: 'Syne', sans-serif !important; font-weight: 600 !important;
  font-size: 0.82rem !important; padding: 6px 14px !important; transition: all 0.15s !important;
}
.stTabs [aria-selected="true"] {
  background: linear-gradient(135deg, var(--accent2), var(--accent)) !important;
  color: #fff !important; box-shadow: 0 2px 10px rgba(34,197,94,0.3) !important;
}

[data-testid="stDataFrame"] {
  background: var(--glass) !important; border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
}

.glass-card {
  background: var(--glass); border: 1px solid var(--border);
  border-radius: var(--radius); backdrop-filter: blur(16px);
  box-shadow: var(--shadow); padding: 1.2rem 1.4rem;
  margin-bottom: 0.85rem; transition: all 0.2s ease;
}
.glass-card:hover { border-color: rgba(34,197,94,0.3); box-shadow: 0 8px 30px rgba(34,197,94,0.1); }

.badge { display: inline-block; padding: 2px 9px; border-radius: 20px; font-size: 0.7rem; font-weight: 700; font-family: 'Syne', sans-serif; text-transform: uppercase; letter-spacing: 0.07em; }
.badge-critical { background:rgba(239,68,68,0.2); color:#f87171; border:1px solid rgba(239,68,68,0.35); }
.badge-high     { background:rgba(245,158,11,0.2); color:#fbbf24; border:1px solid rgba(245,158,11,0.35); }
.badge-medium   { background:rgba(59,130,246,0.2); color:#60a5fa; border:1px solid rgba(59,130,246,0.35); }
.badge-low      { background:rgba(34,197,94,0.15); color:#4ade80; border:1px solid rgba(34,197,94,0.28); }

.risk-bar-wrap { margin: 4px 0 14px; }
.risk-bar-bg   { background:rgba(255,255,255,0.06); border-radius:8px; height:9px; overflow:hidden; }
.risk-bar-fill { height:100%; border-radius:8px; transition:width 0.7s ease; }
.risk-label    { display:flex; justify-content:space-between; font-size:0.76rem; color:var(--text2); margin-bottom:5px; }

.stat-pill { background:rgba(34,197,94,0.07); border:1px solid rgba(34,197,94,0.14); border-radius:12px; padding:12px 8px; text-align:center; }
.stat-val  { font-size:1.5rem; font-weight:700; font-family:'Syne',sans-serif; line-height:1.1; }
.stat-lbl  { font-size:0.7rem; color:var(--text2); margin-top:3px; text-transform:uppercase; letter-spacing:0.06em; }

@keyframes flash-red {
  0%,100% { box-shadow: 0 4px 24px rgba(0,0,0,0.5); border-color: rgba(239,68,68,0.5); }
  50%      { box-shadow: 0 0 24px 4px rgba(239,68,68,0.4); border-color: rgba(239,68,68,0.8); }
}
.alert-flash { animation: flash-red 1.8s infinite; border: 1px solid rgba(239,68,68,0.5) !important; }

::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--g1); }
::-webkit-scrollbar-thumb { background: rgba(34,197,94,0.4); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }

#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden !important; }
[data-testid="stDecoration"] { display: none !important; }
</style>
"""

ALERT_SOUND_JS = """
<script>
function playAlertSound(type) {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator(); const gain = ctx.createGain();
    osc.connect(gain); gain.connect(ctx.destination);
    if (type === 'critical') {
      osc.frequency.setValueAtTime(880, ctx.currentTime);
      osc.frequency.setValueAtTime(660, ctx.currentTime + 0.15);
      osc.frequency.setValueAtTime(880, ctx.currentTime + 0.30);
      gain.gain.setValueAtTime(0.35, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.6);
      osc.start(ctx.currentTime); osc.stop(ctx.currentTime + 0.6);
    } else {
      osc.frequency.setValueAtTime(550, ctx.currentTime);
      gain.gain.setValueAtTime(0.2, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);
      osc.start(ctx.currentTime); osc.stop(ctx.currentTime + 0.3);
    }
  } catch(e) {}
}
window._fg_last = window._fg_last || 0;
function checkAlerts(count, severity) {
  if (count > window._fg_last) { playAlertSound(severity || 'medium'); window._fg_last = count; }
}
</script>
"""


def risk_bar(label: str, value: float) -> str:
    pct = min(100, max(0, float(value)))
    level = "LOW" if pct < 40 else "MODERATE" if pct < 70 else "HIGH" if pct < 85 else "CRITICAL"
    clr = {"LOW": "#22c55e", "MODERATE": "#f59e0b", "HIGH": "#ef4444", "CRITICAL": "#dc2626"}[level]
    return (
        f'<div class="risk-bar-wrap">'
        f'<div class="risk-label"><span>{label}</span>'
        f'<span style="color:{clr};font-weight:600">{pct:.0f}% — {level}</span></div>'
        f'<div class="risk-bar-bg">'
        f'<div class="risk-bar-fill" style="width:{pct}%;background:linear-gradient(90deg,{clr}66,{clr})"></div>'
        f'</div></div>'
    )


def glass_card(content: str, flash: bool = False) -> str:
    cls = "glass-card alert-flash" if flash else "glass-card"
    return f'<div class="{cls}">{content}</div>'


def badge(text: str, level: str = "medium") -> str:
    return f'<span class="badge badge-{level}">{text}</span>'


def weather_grid(w: dict, fire_risk_val: float) -> str:
    temp = w.get("temperature", "—")
    hum  = w.get("humidity", "—")
    wind = w.get("wind_speed", "—")
    cond = w.get("conditions", "—")
    tc = "#4ade80" if isinstance(temp, (int,float)) and temp < 30 else "#fbbf24" if isinstance(temp, (int,float)) and temp < 36 else "#f87171"
    wc = "#60a5fa" if isinstance(wind, (int,float)) and wind < 10 else "#fbbf24" if isinstance(wind, (int,float)) and wind < 18 else "#f87171"
    bar = risk_bar("🔥 Fire Weather Risk", fire_risk_val)
    return (
        '<div style="font-family:Syne,sans-serif;font-size:1rem;color:#22c55e;font-weight:700;margin-bottom:1rem">🌡️ Live Weather</div>'
        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px">'
        f'<div class="stat-pill"><div class="stat-val" style="color:{tc}">{temp}°C</div><div class="stat-lbl">Temperature</div></div>'
        f'<div class="stat-pill"><div class="stat-val" style="color:#60a5fa">{hum}%</div><div class="stat-lbl">Humidity</div></div>'
        f'<div class="stat-pill"><div class="stat-val" style="color:{wc}">{wind}<span style="font-size:0.85rem">m/s</span></div><div class="stat-lbl">Wind Speed</div></div>'
        f'<div class="stat-pill"><div class="stat-val" style="font-size:1rem;color:#e2fce8;padding-top:4px">{cond}</div><div class="stat-lbl">Conditions</div></div>'
        f'</div>{bar}'
    )
