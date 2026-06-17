"""Smart Routing API — A* pathfinding."""
from fastapi import APIRouter, Query
from agents.geospatial_agent import GeospatialAgent

router = APIRouter(prefix="/api/routing", tags=["routing"])
_geo = GeospatialAgent()


@router.get("/route")
async def get_route(
    from_lat: float = Query(...),
    from_lon: float = Query(...),
    to_lat: float = Query(...),
    to_lon: float = Query(...)
):
    return await _geo.get_route(from_lat, from_lon, to_lat, to_lon)
