from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Query
from app.schemas.quality import AnalyzeRequest, RelabelRequest, QualityResult
from app.services.quality_service import quality_service
from app.clients.mongo_client import mongo_client
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
        result = await quality_service.analyze_article(request.content)

        return result
    except Exception as e:
        logger.error(f"Error processing quality analysis request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Đã xảy ra lỗi trong quá trình xử lý: {str(e)}"
        )


@router.put("/relabel", summary="Cập nhật/Sửa nhãn dữ liệu bài viết vào CSDL (MongoDB Atlas)")
async def relabel_quality(request: RelabelRequest):
    """
    Cho phép nhập/cập nhật dữ liệu, sửa nhãn (expected_is_it, expected_quality_level, expected_toxicity)
    và lưu/PUT trực tiếp vào CSDL MongoDB Atlas.
    """
    if not request.content_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mã bài viết (content_id) là bắt buộc."
        )

    try:
        result_dict = {}
        if request.content and request.content.strip():
            analysis_res = await quality_service.analyze_article(request.content)
            result_dict = analysis_res.model_dump()

        result_dict["content_id"] = request.content_id
        if request.content:
            result_dict["content"] = request.content

        label_data = {
            "expected_is_it": request.expected_is_it,
            "expected_quality_level": request.expected_quality_level,
            "expected_toxicity": request.expected_toxicity,
            "notes": request.notes
        }

        # Save/PUT to MongoDB Atlas
        success = await mongo_client.update_label(request.content_id, {**result_dict, **label_data})

        return {
            "status": "success",
            "message": f"Đã PUT và cập nhật nhãn bài viết '{request.content_id}' vào CSDL thành công.",
            "content_id": request.content_id,
            "saved_labels": label_data,
            "mongodb_synced": success
        }
    except Exception as e:
        logger.error(f"Error relabeling quality analysis request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Đã xảy ra lỗi khi cập nhật nhãn CSDL: {str(e)}"
        )


@router.get("/results", summary="Lấy danh sách các bài viết đã phân tích & dán nhãn từ CSDL")
async def get_quality_results(limit: int = Query(50, ge=1, le=500)):
    """
    Lấy danh sách kết quả phân tích & nhãn bài viết đã lưu trong MongoDB Atlas.
    """
    try:
        results = await mongo_client.list_results(limit=limit)
        return {
            "total": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"Error fetching quality results from DB: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi truy vấn CSDL: {str(e)}"
        )

