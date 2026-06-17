"""News service — NewsAPI with fallback static news."""
import httpx, logging
from datetime import datetime, timezone
from core.config import settings
from core.redis_client import set_cache, get_cache

logger = logging.getLogger(__name__)

_FALLBACK = [
    {"title":"Forest fires spike in central India due to dry spell",
     "source":"Environmental Times","url":"#","publishedAt":"2024-06-01"},
    {"title":"Wildlife corridors expanded across Western Ghats",
     "source":"Nature Watch","url":"#","publishedAt":"2024-05-30"},
    {"title":"Anti-poaching tech drones deployed in tiger reserves",
     "source":"Conservation Daily","url":"#","publishedAt":"2024-05-28"},
    {"title":"Elephant population grows 5% in protected reserves",
     "source":"Wildlife Herald","url":"#","publishedAt":"2024-05-25"},
    {"title":"New AI system detects forest fires 3x faster than traditional methods",
     "source":"Tech Ecology","url":"#","publishedAt":"2024-05-22"},
    {"title":"Carbon credit scheme boosts forest conservation funding",
     "source":"Green Finance","url":"#","publishedAt":"2024-05-20"},
]


async def fetch_news(query: str = "forest wildlife conservation") -> list:
    cached = await get_cache("news:latest")
    if cached:
        return cached
    if settings.news_api_key in ("demo", "your_newsapi_key_here", ""):
        await set_cache("news:latest", _FALLBACK, expire=1800)
        return _FALLBACK
    url = "https://newsapi.org/v2/everything"
    params = {"q": query, "apiKey": settings.news_api_key,
              "language": "en", "pageSize": 8, "sortBy": "publishedAt"}
    try:
        async with httpx.AsyncClient(timeout=8) as c:
            r = await c.get(url, params=params); r.raise_for_status()
            articles = r.json().get("articles", [])
            news = [{"title":a["title"],"source":a["source"]["name"],
                     "url":a["url"],"publishedAt":a["publishedAt"][:10]}
                    for a in articles if a.get("title")]
            await set_cache("news:latest", news, expire=1800)
            return news
    except Exception as e:
        logger.warning(f"News API error: {e}")
        await set_cache("news:latest", _FALLBACK, expire=900)
        return _FALLBACK
