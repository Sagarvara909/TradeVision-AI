import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.infrastructure.db.session import get_db
from app.domain.models import UploadedImage
from app.domain.schemas import OCRResult
from app.core.security import get_current_user
from app.services.ocr_service import preprocess_image, extract_text, parse_chart_metadata

router = APIRouter(prefix="/api/v1/ocr", tags=["ocr"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=OCRResult)
async def upload_chart(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    ext = os.path.splitext(file.filename)[1] or ".png"
    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(await file.read())

    image_record = UploadedImage(
        user_id=current_user.id,
        file_path=filepath,
        ocr_status="processing",
    )
    db.add(image_record)
    db.commit()
    db.refresh(image_record)

    try:
        processed_path = preprocess_image(filepath)
        texts = extract_text(processed_path)
        metadata = parse_chart_metadata(texts)

        image_record.ocr_status = "completed" if metadata["symbol"] else "low_confidence"
        db.commit()

        return OCRResult(
            image_id=str(image_record.id),
            symbol=metadata["symbol"],
            exchange=metadata["exchange"],
            timeframe=metadata["timeframe"],
            raw_text_count=len(texts),
        )
    except Exception as e:
        image_record.ocr_status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")