from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    database_url: str
    secret_key: str = "change-this-to-a-random-secret-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    twelve_data_api_key: str
    finnhub_api_key: str

    class Config:
        env_file = ".env"
settings = Settings()