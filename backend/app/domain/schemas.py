from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str= "bearer"

class UserResponse(BaseModel):
    id: str
    email: EmailStr

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class OCRResult(BaseModel):
    image_id: str
    symbol: str | None
    exchange: str | None
    timeframe: str | None
    raw_text_count: int

class QuoteResponse(BaseModel):
    symbol: str
    name: str | None = None
    exchange: str | None = None
    price: float
    change: float | None = None
    percent_change: float | None = None
    volume: int | None = None


class CandleData(BaseModel):
    datetime: str
    open: float
    high: float
    low: float
    close: float
    volume: int | None = None


class TimeSeriesResponse(BaseModel):
    symbol: str
    interval: str
    candles: list[CandleData]