import requests
from fastapi import HTTPException

from app.core.config import Settings

settings = Settings()

BASE_URL = "https://api.twelvedata.com"


def get_quote(symbol: str) -> dict:
    """Fetch current quote data for a symbol."""
    response = requests.get(
        f"{BASE_URL}/quote",
        params={"symbol": symbol, "apikey": settings.twelve_data_api_key},
        timeout=10,
    )
    data = response.json()

    if data.get("status") == "error" or data.get("code"):
        raise HTTPException(
            status_code=400,
            detail=f"Could not fetch quote for '{symbol}': {data.get('message', 'Unknown error')}",
        )

    return data


def get_time_series(symbol: str, interval: str = "1day", output_size: int = 30) -> dict:
    """Fetch historical OHLCV time series for a symbol."""
    response = requests.get(
        f"{BASE_URL}/time_series",
        params={
            "symbol": symbol,
            "interval": interval,
            "outputsize": output_size,
            "apikey": settings.twelve_data_api_key,
        },
        timeout=10,
    )
    data = response.json()

    if data.get("status") == "error" or data.get("code"):
        raise HTTPException(
            status_code=400,
            detail=f"Could not fetch time series for '{symbol}': {data.get('message', 'Unknown error')}",
        )

    return data