# 🌿 Agentic AI Forest Guard — Smart Forest Intelligence System

## 🚀 Quick Start (Docker)

### 1. Prerequisites
- Docker Desktop installed and running
- Git (optional)

### 2. Setup

```bash
# Clone or extract the project
cd forest_guard

# Copy env file
cp .env.example .env

# (Optional) Add real API keys in .env:
#   OPENWEATHER_API_KEY=your_key    # from openweathermap.org (free)
#   NEWS_API_KEY=your_key           # from newsapi.org (free)
# The system works fully without API keys using built-in simulation.
```

### 3. Run

```bash
docker compose up --build
```

### 4. Access

| Service     | URL                              |
|-------------|----------------------------------|
| 🌐 Frontend | http://localhost:8501            |
| ⚙️ Backend  | http://localhost:8000            |
| 📚 API Docs | http://localhost:8000/docs       |
| 🔴 Redis    | localhost:6379                   |

### 5. Login Credentials

| Role      | Username        | Password    |
|-----------|-----------------|-------------|
| Admin     | admin           | admin123    |
| Ranger    | ranger_arjun    | ranger123   |
| Visitor   | visitor_01      | visitor123  |
| Volunteer | volunteer_01    | vol123      |

---

## 🏗️ Architecture

```
forest_guard/
├── docker-compose.yml          # 3-service stack: redis, backend, frontend
├── .env.example                # Environment config template
├── backend/
│   ├── Dockerfile
│   ├── entrypoint.sh           # DB init + agent startup
│   ├── main.py                 # FastAPI app + agent orchestration
│   ├── requirements.txt
│   ├── core/
│   │   ├── config.py           # Settings from env
│   │   ├── database.py         # Async SQLite/SQLAlchemy
│   │   ├── redis_client.py     # Redis pub/sub + cache
│   │   ├── security.py         # JWT auth
│   │   └── seed.py             # Demo data seeding
│   ├── models/
│   │   └── models.py           # All ORM models
│   ├── agents/                 # 11 async AI agents
│   │   ├── base_agent.py
│   │   ├── planner_agent.py    # System orchestrator
│   │   ├── vision_agent.py     # YOLOv8 + tracking
│   │   ├── threat_agent.py     # Fire/poaching prediction
│   │   ├── wildlife_agent.py   # Animal ID tracking
│   │   ├── geospatial_agent.py # A* routing + geofencing
│   │   ├── ranger_agent.py     # Ranger tracking + dispatch
│   │   ├── alert_agent.py      # Alert persistence + dedup
│   │   ├── visitor_agent.py    # QR + overstay detection
│   │   ├── volunteer_agent.py  # Points + community feed
│   │   ├── report_agent.py     # Daily + weekly PDFs
│   │   └── logger_agent.py     # System event logging
│   ├── api/                    # FastAPI routers
│   │   ├── auth.py             # JWT login/register
│   │   ├── alerts.py           # Alert CRUD + stats
│   │   ├── rangers.py          # Ranger ops + dispatch
│   │   ├── visitors.py         # Entry/exit + QR
│   │   ├── volunteers.py       # Reports + leaderboard
│   │   ├── wildlife.py         # Sightings + population
│   │   ├── dashboard.py        # Overview + map data
│   │   ├── reports.py          # PDF generation + download
│   │   ├── ai_chat.py          # Chat + summaries
│   │   └── routing.py          # A* route API
│   └── services/
│       ├── weather_service.py  # OpenWeather + fallback
│       ├── news_service.py     # NewsAPI + fallback
│       └── ai_service.py       # Chat + AI summaries
└── frontend/
    ├── Dockerfile
    ├── requirements.txt
    ├── app.py                  # Main Streamlit app (9 pages)
    ├── api_client.py           # HTTP client for all APIs
    ├── styles.py               # Green glassmorphism CSS
    └── map_utils.py            # Folium map builder
```

## 🤖 Agent Architecture

All 11 agents run as parallel asyncio tasks:

| Agent            | Role                                    |
|------------------|-----------------------------------------|
| PlannerAgent     | Central orchestrator, state management  |
| VisionAgent      | YOLOv8 detection (with simulation mode) |
| ThreatAgent      | Fire/poaching/intrusion risk scoring    |
| WildlifeAgent    | Animal ID tracking + population stats   |
| GeospatialAgent  | A* routing + geo-fence monitoring       |
| RangerAgent      | Live location simulation + dispatch     |
| AlertAgent       | Alert persistence + deduplication       |
| VisitorAgent     | Overstay detection + QR generation      |
| VolunteerAgent   | Points system + report processing       |
| ReportAgent      | Daily + weekly PDF generation           |
| LoggerAgent      | System-wide event logging               |

## 📡 API Endpoints

| Endpoint                       | Description                     |
|--------------------------------|---------------------------------|
| POST /api/auth/token           | JWT login                       |
| POST /api/auth/register        | Register user                   |
| GET  /api/dashboard/overview   | System-wide KPIs                |
| GET  /api/alerts               | List active alerts              |
| GET  /api/rangers              | Ranger status + locations       |
| POST /api/rangers/{id}/dispatch| Emergency dispatch              |
| GET  /api/wildlife/population  | Species population stats        |
| GET  /api/wildlife/heatmap     | Sighting heatmap data           |
| POST /api/ai/chat              | AI chat assistant               |
| GET  /api/reports/summary/weekly| Weekly AI summary              |
| POST /api/reports/generate/weekly| Generate weekly PDF           |
| GET  /api/routing/route        | A* pathfinding                  |

Full interactive docs: http://localhost:8000/docs

## 🛠️ Tech Stack

- **Backend**: FastAPI (async), SQLite, SQLAlchemy
- **Frontend**: Streamlit, Folium/OpenStreetMap, Plotly
- **AI/CV**: YOLOv8, OpenCV (with simulation fallback)
- **Messaging**: Redis Pub/Sub + caching
- **Auth**: JWT (python-jose + passlib)
- **Reports**: ReportLab PDF
- **Maps**: Folium + OpenStreetMap (no Google Maps)
- **Deploy**: Docker Compose

## 🐛 Troubleshooting

**Backend not starting:**
```bash
docker compose logs backend
```

**Redis connection issues:**
```bash
docker compose logs redis
docker compose restart backend
```

**Frontend can't reach backend:**
- Ensure both containers are healthy: `docker compose ps`
- Check BACKEND_URL env in docker-compose.yml

**Reset everything:**
```bash
docker compose down -v
docker compose up --build
```
