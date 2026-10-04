from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.ocr import router as ocr_router
from app.api.v1.auth import router as auth_router
from app.api.v1.market import router as market_router
from app.api.v1.reports import router as reports_router
from app.api.v1.chat import router as chat_router

app = FastAPI(title="TradeVision AI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080","http://localhost:8082"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(ocr_router)
app.include_router(market_router)
app.include_router(reports_router)
app.include_router(chat_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}