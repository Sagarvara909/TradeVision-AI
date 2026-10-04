from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


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


class TechnicalAnalysisResponse(BaseModel):
    symbol: str
    ema20: float
    ema50: float | None
    rsi: float
    macd: float
    macd_signal: float
    macd_histogram: float
    trend: str
    support: float | None
    resistance: float | None
    latest_volume: int
    average_volume: int | None
    volume_ratio: float | None
    above_average_volume: bool | None


class SentimentResponse(BaseModel):
    label: str
    score: float
    article_count: int
    headlines: list[dict]


# Inherits every technical field (ema20, ema50, macd, support, volume, etc.)
# from TechnicalAnalysisResponse, then adds the risk/confidence layer on top.
# This is what fixes the LLM report showing "unavailable" for indicators that
# were already being calculated but never reached this response before.
class RiskAnalysisResponse(TechnicalAnalysisResponse):
    volatility_pct: float
    sentiment: SentimentResponse
    confidence_score: int
    risk_level: str
    reasoning: list[str]


class ReportRequest(BaseModel):
    image_id: str
    symbol: str
    timeframe: str = "1day"
    exchange: str | None = None  # e.g. "NSE", "BSE", "NASDAQ" — needed to resolve Indian tickers


class ReportResponse(BaseModel):
    id: str
    image_id: str
    symbol: str
    timeframe: str
    confidence_score: int
    risk_level: str
    reasoning: list[str]
    indicators: dict
    llm_report: str
    llm_model: str | None = None
    unsupported_numbers: list[str] = []
    created_at: str


class ChatMessageRequest(BaseModel):
    message: str


class ChatMessageResponse(BaseModel):
    id: str
    role: str  # "user" or "assistant"
    content: str
    created_at: str
    llm_model: str | None = None  # set only on "assistant" messages
    unsupported_numbers: list[str] = []  # set only on "assistant" messages


class ChatHistoryResponse(BaseModel):
    report_id: str
    messages: list[ChatMessageResponse]