"""
Central configuration for Forest Guard system.
Reads from .env file via pydantic-settings.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    # API Keys
    openweather_api_key: str = Field(default="demo_key", env="OPENWEATHER_API_KEY")
    news_api_key: str = Field(default="demo_key", env="NEWS_API_KEY")

    # JWT
    secret_key: str = Field(default="forest_guard_super_secret_key_change_in_production", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=1440, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    # Redis
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./database/forest_guard.db",
        env="DATABASE_URL"
    )

    # FastAPI
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    debug: bool = Field(default=True, env="DEBUG")

    # Forest Config
    forest_name: str = Field(default="GreenShield Forest Reserve", env="FOREST_NAME")
    forest_center_lat: float = Field(default=11.4916, env="FOREST_CENTER_LAT")
    forest_center_lon: float = Field(default=76.9294, env="FOREST_CENTER_LON")
    forest_area_km2: float = Field(default=1200.0, env="FOREST_AREA_KM2")

    # Alert Thresholds
    fire_risk_threshold: int = Field(default=70, env="FIRE_RISK_THRESHOLD")
    poaching_risk_threshold: int = Field(default=60, env="POACHING_RISK_THRESHOLD")
    overstay_hours: int = Field(default=8, env="OVERSTAY_HOURS")

    # Paths
    reports_dir: str = Field(default="./reports", env="REPORTS_DIR")
    logs_dir: str = Field(default="./logs", env="LOGS_DIR")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()

# Ensure directories exist
os.makedirs(settings.reports_dir, exist_ok=True)
os.makedirs(settings.logs_dir, exist_ok=True)
os.makedirs("./database", exist_ok=True)
