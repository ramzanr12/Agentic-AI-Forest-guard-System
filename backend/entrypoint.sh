#!/bin/bash
set -e

echo "=========================================="
echo " Agentic AI Forest Guard - Backend"
echo "=========================================="

# Wait for Redis
echo "Waiting for Redis..."
until python -c "import redis; r = redis.Redis(host='${REDIS_HOST:-redis}', port=${REDIS_PORT:-6379}); r.ping()" 2>/dev/null; do
    sleep 1
    echo "Redis not ready, retrying..."
done
echo "Redis is ready."

# Initialize database
echo "Initializing database..."
python -c "
import asyncio
import sys
sys.path.insert(0, '/app')
from core.database import init_db
asyncio.run(init_db())
print('Database initialized.')
"

# Seed / repair default data
echo "Seeding default data..."
python -c "
import asyncio
import sys
sys.path.insert(0, '/app')
from core.seed import seed_database
asyncio.run(seed_database())
"

echo "Starting FastAPI server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2 --loop asyncio
