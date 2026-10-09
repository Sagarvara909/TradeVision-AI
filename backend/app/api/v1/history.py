from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.infrastructure.db.session import get_db
from app.domain.models import Report, AnalysisHistory
from app.domain.schemas import HistoryEntryResponse, HistoryListResponse


router = APIRouter(prefix="/api/v1/history", tags=["history"])


@router.get("", response_model=HistoryListResponse)
def get_history(
    limit: int = Query(default=50, ge=1, le=200),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    The user's reports, most-recently-viewed first. Each report appears
    once, at the time of its latest view — opening an old report again
    bumps it back to the top, same as a browser's history page.
    """
    last_viewed_subq = (
        db.query(
            AnalysisHistory.report_id.label("report_id"),
            func.max(AnalysisHistory.viewed_at).label("last_viewed_at"),
        )
        .group_by(AnalysisHistory.report_id)
        .subquery()
    )

    rows = (
        db.query(Report, last_viewed_subq.c.last_viewed_at)
        .join(last_viewed_subq, Report.id == last_viewed_subq.c.report_id)
        .filter(Report.user_id == current_user.id)
        .order_by(last_viewed_subq.c.last_viewed_at.desc())
        .limit(limit)
        .all()
    )

    entries = []
    for report, last_viewed_at in rows:
        indicators = report.indicators or {}
        entries.append(
            HistoryEntryResponse(
                report_id=report.id,
                symbol=report.symbol,
                timeframe=report.timeframe,
                trend=indicators.get("trend"),
                confidence_score=indicators.get("confidence_score", report.confidence_score),
                risk_level=indicators.get("risk_level", "unknown"),
                created_at=report.created_at.isoformat(),
                last_viewed_at=last_viewed_at.isoformat(),
            )
        )

    return HistoryListResponse(entries=entries)