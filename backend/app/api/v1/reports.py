import html as html_module
import re

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from weasyprint import HTML as WeasyHTML

from app.core.security import get_current_user
from app.infrastructure.db.session import get_db
from app.domain.models import UploadedImage, Report, AnalysisHistory
from app.domain.schemas import ReportRequest, ReportResponse
from app.services.risk_service import analyze_symbol, InsufficientDataError
from app.services.llm_service import generate_report, LLMServiceError


router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


def _log_view(report_id: str, db: Session) -> None:
    """Record that this report was viewed, for the Analysis History page.
    Called both when a report is first created (creating it IS a view) and
    whenever it's fetched again later, so re-opening an old report bumps it
    back to the top of "recently viewed"."""
    db.add(AnalysisHistory(report_id=report_id))
    db.commit()


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
    _log_view(report.id, db)

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

    _log_view(report.id, db)

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


def _render_report_html(report: Report) -> str:
    """
    Build a small, self-contained HTML document for weasyprint to render.
    Everything from the LLM report text is HTML-escaped first, and only
    then is our own **bold** markdown turned into <strong> tags — so no
    stray HTML the model happened to produce can leak through unescaped.
    """
    indicators = report.indicators or {}
    reasoning = indicators.get("reasoning", [])
    confidence = indicators.get("confidence_score", report.confidence_score)
    risk_level = indicators.get("risk_level", "unknown")
    trend = indicators.get("trend", "N/A")

    body = html_module.escape(report.llm_report or "")
    body = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", body)
    paragraphs = "".join(
        f"<p>{p.strip().replace(chr(10), '<br>')}</p>" for p in body.split("\n\n") if p.strip()
    )

    reasoning_html = "".join(f"<li>{html_module.escape(r)}</li>" for r in reasoning)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    body {{ font-family: Helvetica, Arial, sans-serif; color: #1a1a1a; padding: 32px; }}
    h1 {{ font-size: 20px; margin-bottom: 4px; }}
    .meta {{ color: #666; font-size: 11px; margin-bottom: 24px; }}
    .score-box {{ display: inline-block; border: 1px solid #ddd; border-radius: 8px; padding: 12px 20px; margin-bottom: 20px; }}
    .score {{ font-size: 28px; font-weight: bold; }}
    .risk {{ text-transform: capitalize; color: #b45309; font-size: 12px; }}
    h2 {{ font-size: 13px; text-transform: uppercase; letter-spacing: 1px; color: #6366f1; margin-top: 24px; margin-bottom: 8px; }}
    ul {{ font-size: 12px; color: #444; padding-left: 18px; }}
    p {{ font-size: 12px; line-height: 1.6; color: #222; }}
    .disclaimer {{ margin-top: 32px; padding-top: 12px; border-top: 1px solid #ddd; font-size: 10px; color: #888; }}
</style>
</head>
<body>
    <h1>TradeVision AI &mdash; Analysis Report</h1>
    <div class="meta">
        {html_module.escape(report.symbol)} &middot; {html_module.escape(report.timeframe)} &middot;
        Trend: {html_module.escape(str(trend))} &middot;
        Generated {report.created_at.strftime('%Y-%m-%d %H:%M UTC')}
    </div>

    <div class="score-box">
        <div class="score">{confidence}/100</div>
        <div class="risk">{html_module.escape(str(risk_level))} risk</div>
    </div>

    <h2>Reasoning</h2>
    <ul>{reasoning_html}</ul>

    <h2>Explainable Report</h2>
    {paragraphs}

    <div class="disclaimer">
        This report is generated for educational and decision-support purposes only.
        It is not financial advice, and it does not predict future price movements.
    </div>
</body>
</html>"""


@router.get("/{report_id}/pdf")
def download_report_pdf(
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

    html_str = _render_report_html(report)
    pdf_bytes = WeasyHTML(string=html_str).write_pdf()

    filename = f"TradeVision_{report.symbol}_{report.created_at.strftime('%Y%m%d')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )