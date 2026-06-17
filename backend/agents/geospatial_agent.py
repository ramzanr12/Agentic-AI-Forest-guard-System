"""Geospatial Agent — A* routing, geo-fencing, zone management."""
import asyncio, heapq, math, random
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional, Set
from agents.base_agent import BaseAgent
from core.redis_client import set_cache, get_cache


# ── A* Pathfinder ──────────────────────────────────────────────────────────
class _Node:
    __slots__ = ("r","c","g","h","f","parent","walkable")
    def __init__(self, r, c):
        self.r=r; self.c=c
        self.g=1e9; self.h=0; self.f=1e9
        self.parent=None; self.walkable=True
    def __lt__(self, o): return self.f < o.f
    def __eq__(self, o): return self.r==o.r and self.c==o.c
    def __hash__(self): return hash((self.r, self.c))


class AStarGrid:
    ROWS, COLS = 50, 50
    def __init__(self):
        self.grid = [[_Node(r,c) for c in range(self.COLS)] for r in range(self.ROWS)]
        # Restricted blocks (core sanctuary, rivers)
        for r in range(15,25):
            for c in range(10,20):
                self.grid[r][c].walkable = False
        for r in range(30,38):
            for c in range(25,35):
                self.grid[r][c].walkable = False

    def _reset(self):
        for row in self.grid:
            for n in row:
                n.g=1e9; n.h=0; n.f=1e9; n.parent=None

    def _neighbors(self, n):
        dirs = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
        out = []
        for dr,dc in dirs:
            nr,nc = n.r+dr, n.c+dc
            if 0<=nr<self.ROWS and 0<=nc<self.COLS and self.grid[nr][nc].walkable:
                out.append(self.grid[nr][nc])
        return out

    def find(self, s: Tuple[int,int], e: Tuple[int,int]) -> Optional[List[Tuple[int,int]]]:
        self._reset()
        sn, en = self.grid[s[0]][s[1]], self.grid[e[0]][e[1]]
        if not sn.walkable or not en.walkable:
            return None
        sn.g=0; sn.h=abs(sn.r-en.r)+abs(sn.c-en.c); sn.f=sn.h
        heap=[sn]; closed: Set[_Node]=set()
        while heap:
            cur=heapq.heappop(heap)
            if cur==en:
                path=[]
                while cur: path.append((cur.r,cur.c)); cur=cur.parent
                return list(reversed(path))
            closed.add(cur)
            for nb in self._neighbors(cur):
                if nb in closed: continue
                tg=cur.g+1
                if tg<nb.g:
                    nb.parent=cur; nb.g=tg
                    nb.h=abs(nb.r-en.r)+abs(nb.c-en.c); nb.f=nb.g+nb.h
                    if nb not in heap: heapq.heappush(heap,nb)
        return None

    def to_latlon(self, pos, clat=11.4916, clon=76.9294, ext=0.15):
        lat=clat-ext+(pos[0]/self.ROWS)*2*ext
        lon=clon-ext+(pos[1]/self.COLS)*2*ext
        return round(lat,6), round(lon,6)

    def from_latlon(self, lat, lon, clat=11.4916, clon=76.9294, ext=0.15):
        r=int((lat-(clat-ext))/(2*ext)*self.ROWS)
        c=int((lon-(clon-ext))/(2*ext)*self.COLS)
        return max(0,min(self.ROWS-1,r)), max(0,min(self.COLS-1,c))


# ── Geo-fence ──────────────────────────────────────────────────────────────
class GeoFence:
    def __init__(self, name, clat, clon, radius_km, ftype="restricted"):
        self.name=name; self.clat=clat; self.clon=clon
        self.radius_km=radius_km; self.ftype=ftype

    def dist(self, lat, lon) -> float:
        R=6371
        dl=math.radians(lat-self.clat); dln=math.radians(lon-self.clon)
        a=math.sin(dl/2)**2+math.cos(math.radians(self.clat))*math.cos(math.radians(lat))*math.sin(dln/2)**2
        return R*2*math.atan2(math.sqrt(a),math.sqrt(1-a))

    def violated(self, lat, lon) -> bool:
        return self.ftype=="restricted" and self.dist(lat,lon)<self.radius_km


class GeospatialAgent(BaseAgent):
    def __init__(self):
        super().__init__("GeospatialAgent")
        self.grid = AStarGrid()
        self.fences: Dict[str, GeoFence] = {
            "Core-Sanctuary":       GeoFence("Core-Sanctuary",     11.4916,76.9294,2.0),
            "Tiger-Reserve-Alpha":  GeoFence("Tiger-Reserve-Alpha",11.5200,76.9500,1.5),
            "Water-Source":         GeoFence("Water-Source",        11.4650,76.9100,0.8),
            "Poaching-Hotspot-1":   GeoFence("Poaching-Hotspot-1", 11.4800,76.9600,1.2,"monitoring"),
        }
        self.zones = self._build_zones()

    def _build_zones(self):
        offsets = [
            ("Zone-A",-0.05,-0.05,"low"),
            ("Zone-B", 0.05,-0.05,"medium"),
            ("Zone-C", 0.05, 0.05,"high"),
            ("Zone-D",-0.05, 0.05,"medium"),
            ("Core-Zone",0.0,0.0,"restricted"),
        ]
        zones = []
        for name,dlat,dlon,risk in offsets:
            cl=11.4916+dlat; co=76.9294+dlon; e=0.04
            zones.append({
                "name":name, "risk_level":risk,
                "center":[cl,co],
                "geojson":{"type":"Feature",
                    "properties":{"name":name,"risk":risk},
                    "geometry":{"type":"Polygon","coordinates":[[
                        [co-e,cl-e],[co+e,cl-e],[co+e,cl+e],[co-e,cl+e],[co-e,cl-e]
                    ]]}}
            })
        return zones

    async def run(self):
        await self.start()
        await set_cache("geo:zones", self.zones, expire=3600)
        while self._running:
            try:
                await self._check_fences()
                await asyncio.sleep(20)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"GeospatialAgent error: {e}")
                await asyncio.sleep(15)

    async def _check_fences(self):
        entities = (await get_cache("rangers:live") or []) + (await get_cache("visitors:live") or [])
        for ent in entities:
            lat=ent.get("lat",0); lon=ent.get("lon",0); eid=ent.get("id","?")
            for fname,fence in self.fences.items():
                if fence.violated(lat, lon):
                    await self.emit("alerts:new",{
                        "alert_type":"geofence_violation","severity":"high",
                        "description":f"Entity {eid} entered restricted zone: {fname}",
                        "lat":lat,"lon":lon,"zone":fname
                    })

    async def get_route(self, flat,flon,tlat,tlon) -> dict:
        sg=self.grid.from_latlon(flat,flon); eg=self.grid.from_latlon(tlat,tlon)
        path=self.grid.find(sg,eg)
        if not path:
            return {"success":False,"message":"No path — blocked by restricted zones"}
        ll=[self.grid.to_latlon(p) for p in path]
        dist=sum(math.sqrt((ll[i+1][0]-ll[i][0])**2+(ll[i+1][1]-ll[i][1])**2)*111
                 for i in range(len(ll)-1))
        return {"success":True,
                "path":[{"lat":p[0],"lon":p[1]} for p in ll],
                "waypoints":len(ll),
                "distance_km":round(dist,2),
                "estimated_minutes":round(dist/5*60)}
