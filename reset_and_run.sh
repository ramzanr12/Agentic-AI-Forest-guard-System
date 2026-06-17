#!/bin/bash
# ============================================================
#  Forest Guard — Full Reset & Restart
#  Run this once to clear stale data and get a clean start
# ============================================================
set -e
echo ""
echo "🌿 Forest Guard — Reset & Restart"
echo "=================================================="

echo ""
echo "► Step 1: Stopping any running containers..."
docker compose down --remove-orphans 2>/dev/null || true

echo ""
echo "► Step 2: Removing stale database volume (fixes bcrypt seed issue)..."
docker volume rm forest_guard_backend_db 2>/dev/null || true

echo ""
echo "► Step 3: Rebuilding images with fixed dependencies..."
docker compose build --no-cache

echo ""
echo "► Step 4: Starting all services..."
docker compose up -d

echo ""
echo "► Step 5: Waiting for backend to be healthy..."
for i in $(seq 1 30); do
  STATUS=$(docker inspect --format='{{.State.Health.Status}}' forest_backend 2>/dev/null || echo "starting")
  if [ "$STATUS" = "healthy" ]; then
    echo "   ✅ Backend is healthy!"
    break
  fi
  echo "   ⏳ Waiting... ($i/30) — status: $STATUS"
  sleep 5
done

echo ""
echo "=================================================="
echo "  ✅ Forest Guard is ready!"
echo ""
echo "  Frontend  →  http://localhost:8501"
echo "  Backend   →  http://localhost:8000"
echo "  API Docs  →  http://localhost:8000/docs"
echo ""
echo "  Demo Accounts:"
echo "  👑 admin          / admin123"
echo "  👮 ranger_arjun   / ranger123"
echo "  🚶 visitor_01     / visitor123"
echo "  🤝 volunteer_01   / vol123"
echo "=================================================="
echo ""
echo "  To watch logs: docker compose logs -f"
echo "  To stop:       docker compose down"
