from fastapi import APIRouter, HTTPException, status
from app.schemas.quality import AnalyzeRequest, QualityResult
from app.services.quality_service import quality_service
from app.core.logging import logger

router = APIRouter(prefix="/api/v1/quality", tags=["Quality Analysis"])


@router.post("/analyze", response_model=QualityResult, summary="Phân tích & Đánh giá chất lượng bài viết")
async def analyze_quality(request: AnalyzeRequest):
    """
    Nhận nội dung bài viết và thực hiện pipeline:
    1. Làm sạch HTML, loại bỏ control char, bảo vệ Code/URL, demojize Emoji.
    2. Chuẩn hóa từ vựng (Aho-Corasick & Elasticsearch Fuzzy).
    3. Tách từ tiếng Việt (Underthesea).
    4. Phân loại IT Domain & Nội dung độc hại (ML models).
    5. Đánh giá chất lượng bằng Rule Engine độc lập.
    6. Tính điểm Quality Score & phân mức chất lượng.
    """
    if not request.content or not request.content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nội dung bài viết không được để trống."
        )

    try:
        result = quality_service.analyze_article(request.content)
        return result
    except Exception as e:
        logger.error(f"Error processing quality analysis request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Đã xảy ra lỗi trong quá trình xử lý: {str(e)}"
        )
