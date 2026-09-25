"""Application configuration settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for backend services."""

    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"

    # Default receiver parameters
    RECEIVER_BANDWIDTH_HZ: float = 500_000_000.0  # 500 MHz
    DEFAULT_DWELL_TIME_MS: float = 25.0           # 25 ms
    DEFAULT_SCAN_STRATEGY: str = "round_robin"

    # Simulation engine parameters
    SIMULATION_TICK_MS: float = 50.0             # 50 ms tick interval
    SIMULATION_SPEED: float = 1.0                # Speed multiplier
    AUTO_START_SIMULATION: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
