from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    secret_key: str = "change-this-to-a-random-secret-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    # No longer required — market data now comes from yfinance (free, no key).
    # Kept optional so an existing .env with this key still loads fine.
    twelve_data_api_key: str | None = None
    finnhub_api_key: str
    gemini_api_key: str

    # Which Gemini model to use for report generation, and which ones to try
    # next if the primary is overloaded (503) or rate-limited (429).
    # Update these any time by running try_models.py again.
    gemini_model: str = "gemini-3.6-flash"
    gemini_fallback_models: list[str] = ["gemini-3.1-flash-lite"]

    class Config:
        env_file = ".env"


settings = Settings()