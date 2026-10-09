from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.infrastructure.db.session import get_db
from app.domain.models import Watchlist
from app.domain.schemas import WatchlistAddRequest, WatchlistItemResponse, WatchlistListResponse
from app.services.market_service import get_quote


router = APIRouter(prefix="/api/v1/watchlist", tags=["watchlist"])


def _safe_quote(symbol: str, exchange: str | None) -> dict:
    """Fetch a live quote, but never let one bad/delisted symbol break the
    whole watchlist listing — return an error message for that row instead."""
    try:
        q = get_quote(symbol, exchange)
        return {
            "price": float(q["close"]) if q.get("close") else None,
            "change": float(q["change"]) if q.get("change") else None,
            "percent_change": float(q["percent_change"]) if q.get("percent_change") else None,
            "quote_error": None,
        }
    except HTTPException as e:
        return {"price": None, "change": None, "percent_change": None, "quote_error": e.detail}
    except Exception as e:
        return {"price": None, "change": None, "percent_change": None, "quote_error": str(e)}


@router.post("", response_model=WatchlistItemResponse)
def add_to_watchlist(
    payload: WatchlistAddRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    symbol = payload.symbol.strip().upper()
    exchange = (payload.exchange or "").strip().upper() or None

    existing = (
        db.query(Watchlist)
        .filter(
            Watchlist.user_id == current_user.id,
            Watchlist.symbol == symbol,
            Watchlist.exchange == exchange,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail=f"{symbol} is already on your watchlist.")

    item = Watchlist(user_id=current_user.id, symbol=symbol, exchange=exchange)
    db.add(item)
    db.commit()
    db.refresh(item)

    quote = _safe_quote(symbol, exchange)
    return WatchlistItemResponse(
        id=item.id, symbol=item.symbol, exchange=item.exchange,
        added_at=item.added_at.isoformat(), **quote,
    )


@router.get("", response_model=WatchlistListResponse)
def list_watchlist(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = (
        db.query(Watchlist)
        .filter(Watchlist.user_id == current_user.id)
        .order_by(Watchlist.added_at.desc())
        .all()
    )

    results = []
    for item in items:
        quote = _safe_quote(item.symbol, item.exchange)
        results.append(
            WatchlistItemResponse(
                id=item.id, symbol=item.symbol, exchange=item.exchange,
                added_at=item.added_at.isoformat(), **quote,
            )
        )
    return WatchlistListResponse(items=results)


@router.delete("/{item_id}")
def remove_from_watchlist(
    item_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = (
        db.query(Watchlist)
        .filter(Watchlist.id == item_id, Watchlist.user_id == current_user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found.")
    db.delete(item)
    db.commit()
    return {"status": "removed"}