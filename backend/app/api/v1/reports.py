from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.infrastructure.db.session import get_db
from app.domain.models import UploadedImage, Report
from app.domain.schemas import ReportRequest, ReportResponse
from app.services.risk_service import analyze_symbol, InsufficientDataError
from app.services.llm_service import generate_report, LLMServiceError


router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.post("", response_model=ReportResponse)
def create_report(
    payload: ReportRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # The image must exist and belong to the caller, since Report.image_id is
    # a required foreign key and reports are per-user data.
    image = (
        db.query(UploadedImage)
        .filter(UploadedImage.id == payload.image_id, UploadedImage.user_id == current_user.id)
        .first()
    )
    if not image:
        raise HTTPException(status_code=404, detail="Uploaded image not found.")

    try:
        analysis = analyze_symbol(
            payload.symbol, interval=payload.timeframe, exchange=payload.exchange
        )
    except InsufficientDataError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # If Gemini fails, we still save the (already-computed) analysis instead
    # of losing it, and tell the caller plainly what happened. The confidence
    # score and reasoning trail don't depend on the LLM at all.
    llm_model = None
    unsupported_numbers: list[str] = []
    try:
        llm_result = generate_report(analysis)
        llm_text = llm_result["report"]
        llm_model = llm_result["model"]
        unsupported_numbers = llm_result["unsupported_numbers"]
    except LLMServiceError as e:
        llm_text = f"[Report generation failed: {e}]"

    report = Report(
        user_id=current_user.id,
        image_id=image.id,
        symbol=payload.symbol,
        timeframe=payload.timeframe,
        confidence_score=analysis["confidence_score"],
        indicators=analysis,
        llm_report=llm_text,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return ReportResponse(
        id=report.id,
        image_id=report.image_id,
        symbol=report.symbol,
        timeframe=report.timeframe,
        confidence_score=analysis["confidence_score"],
        risk_level=analysis["risk_level"],
        reasoning=analysis["reasoning"],
        indicators=analysis,
        llm_report=report.llm_report,
        llm_model=llm_model,
        unsupported_numbers=unsupported_numbers,
        created_at=report.created_at.isoformat(),
    )


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = (
        db.query(Report)
        .filter(Report.id == report_id, Report.user_id == current_user.id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    indicators = report.indicators or {}
    return ReportResponse(
        id=report.id,
        image_id=report.image_id,
        symbol=report.symbol,
        timeframe=report.timeframe,
        confidence_score=indicators.get("confidence_score", report.confidence_score),
        risk_level=indicators.get("risk_level", "unknown"),
        reasoning=indicators.get("reasoning", []),
        indicators=indicators,
        llm_report=report.llm_report or "",
        created_at=report.created_at.isoformat(),
    )