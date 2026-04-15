import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_SQLITE_URL = f"sqlite:///{BASE_DIR / 'pattern_prediction.db'}"


@dataclass(frozen=True)
class Settings:
    app_env: str
    app_name: str
    jwt_secret_key: str
    cors_allowed_origins: str
    db_url: str


settings = Settings(
    app_env=os.getenv("APP_ENV", "dev"),
    app_name=os.getenv("APP_NAME", "Cattle Disease Pattern Prediction API"),
    jwt_secret_key=os.getenv("JWT_SECRET_KEY", "change-me-in-production"),
    cors_allowed_origins=os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501"),
    db_url=os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL),
)
