"""Central configuration — reads environment variables."""
import os
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # JWT
    secret_key: str = Field(default="forest_guard_super_secret_key_2024", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=1440, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    # External APIs
    openweather_api_key: str = Field(default="demo", env="OPENWEATHER_API_KEY")
    news_api_key: str = Field(default="demo", env="NEWS_API_KEY")

    # Redis
    redis_host: str = Field(default="redis", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:////app/database/forest_guard.db",
        env="DATABASE_URL"
    )

    # Forest
    forest_name: str = Field(default="GreenShield Forest Reserve", env="FOREST_NAME")
    forest_center_lat: float = Field(default=11.4916, env="FOREST_CENTER_LAT")
    forest_center_lon: float = Field(default=76.9294, env="FOREST_CENTER_LON")
    forest_area_km2: float = Field(default=1200.0, env="FOREST_AREA_KM2")

    # Thresholds
    fire_risk_threshold: int = Field(default=70, env="FIRE_RISK_THRESHOLD")
    poaching_risk_threshold: int = Field(default=60, env="POACHING_RISK_THRESHOLD")
    overstay_hours: int = Field(default=8, env="OVERSTAY_HOURS")

    # Paths
    reports_dir: str = Field(default="/app/reports", env="REPORTS_DIR")
    logs_dir: str = Field(default="/app/logs", env="LOGS_DIR")
    uploads_dir: str = Field(default="/app/static/uploads", env="UPLOADS_DIR")

    debug: bool = Field(default=True, env="DEBUG")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

# Ensure directories exist
for d in [settings.reports_dir, settings.logs_dir, settings.uploads_dir, "/app/database"]:
    os.makedirs(d, exist_ok=True)
