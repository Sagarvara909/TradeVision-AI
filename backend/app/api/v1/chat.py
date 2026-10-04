from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.infrastructure.db.session import get_db
from app.domain.models import Report, ChatMessage
from app.domain.schemas import ChatMessageRequest, ChatMessageResponse, ChatHistoryResponse
from app.services.chat_service import answer_question
from app.services.llm_service import LLMServiceError


router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


def _get_owned_report(report_id: str, current_user, db: Session) -> Report:
    report = (
        db.query(Report)
        .filter(Report.id == report_id, Report.user_id == current_user.id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    return report


@router.post("/{report_id}", response_model=ChatMessageResponse)
def ask_question(
    report_id: str,
    payload: ChatMessageRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = _get_owned_report(report_id, current_user, db)

    if not payload.message.strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty.")

    # Prior turns, oldest first, so the model sees the conversation in order.
    prior = (
        db.query(ChatMessage)
        .filter(ChatMessage.report_id == report.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in prior]

    user_message = ChatMessage(report_id=report.id, role="user", content=payload.message)
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    try:
        result = answer_question(
            indicators=report.indicators or {},
            report_text=report.llm_report or "",
            history=history,
            question=payload.message,
        )
        answer_text = result["answer"]
        llm_model = result["model"]
        unsupported_numbers = result["unsupported_numbers"]
    except LLMServiceError as e:
        # Still save a reply so the thread stays coherent, and the person
        # can see exactly what went wrong rather than a silently missing turn.
        answer_text = f"[Could not answer: {e}]"
        llm_model = None
        unsupported_numbers = []

    assistant_message = ChatMessage(report_id=report.id, role="assistant", content=answer_text)
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    return ChatMessageResponse(
        id=assistant_message.id,
        role=assistant_message.role,
        content=assistant_message.content,
        created_at=assistant_message.created_at.isoformat(),
        llm_model=llm_model,
        unsupported_numbers=unsupported_numbers,
    )


@router.get("/{report_id}", response_model=ChatHistoryResponse)
def get_history(
    report_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = _get_owned_report(report_id, current_user, db)

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.report_id == report.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    return ChatHistoryResponse(
        report_id=report.id,
        messages=[
            ChatMessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                created_at=m.created_at.isoformat(),
            )
            for m in messages
        ],
    )