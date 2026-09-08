from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# Re-export core sub-domain schemas for convenient access
from app.schemas.safety import SafetyScores, SafetyClassification, ToxicityResult
from app.schemas.domain import ITRelevanceLabel, ITDomainLabel, ITRelevanceResult, ITDomainResult
from app.schemas.code_analysis import CodeAnalysisResult
from app.schemas.semantic import SemanticResult, DuplicateAnalysisResult, DuplicateType, SimilarityQueryRequest, SimilaritySearchResult
from app.schemas.tags import TagExtractionItem, TagExtractionResult
from app.schemas.technical_depth import TechnicalDepthResult
from app.schemas.user_reputation import UserRankEnum, UserFeatureVector, UserScoreBreakdown, PromotionEligibility, UserReputationResult
from app.schemas.mlops import DatasetSample, ModelMetrics, ModelMetadata


class AnalyzeRequest(BaseModel):
    content: str = Field(..., description="Nội dung bài viết cần phân tích và chấm điểm", min_length=1)
    content_id: Optional[str] = Field(None, description="Mã bài viết (nếu có)")
    user_id: Optional[str] = Field(None, description="Mã tác giả/người dùng (nếu có)")


class RelabelRequest(BaseModel):
    content_id: str = Field(..., description="Mã bài viết/kết quả phân tích cần sửa nhãn")
    content: Optional[str] = Field(None, description="Nội dung bài viết (nếu tạo mới hoặc cập nhật)")
    expected_is_it: Optional[bool] = Field(None, description="Nhãn thuộc IT domain đúng (True/False)")
    expected_quality_level: Optional[str] = Field(None, description="Mức chất lượng đúng (excellent, good, average, poor)")
    expected_toxicity: Optional[str] = Field(None, description="Mức độ độc hại đúng (safe, toxic, suspicious)")
    notes: Optional[str] = Field(None, description="Ghi chú mô tả nhãn")


class ArticleStatistics(BaseModel):
    word_count: int = Field(0, description="Tổng số từ trong bài")
    sentence_count: int = Field(0, description="Tổng số câu trong bài")
    paragraph_count: int = Field(0, description="Tổng số đoạn văn")
    code_blocks: int = Field(0, description="Số lượng thẻ/khối mã nguồn")
    urls: int = Field(0, description="Số lượng đường dẫn URL")
    emoji_count: int = Field(0, description="Số lượng Emoji")
    teencode_count: int = Field(0, description="Số từ teencode đã phát hiện")
    typo_count: int = Field(0, description="Số từ viết sai chính tả đã phát hiện")


class QualityIssue(BaseModel):
    type: str = Field(..., description="Loại lỗi (spelling, teencode, spam, structure, ratio)")
    original: str = Field(..., description="Từ/cụm từ gốc")
    corrected: Optional[str] = Field(None, description="Từ/cụm từ gợi ý sửa")
    confidence: Optional[float] = Field(None, description="Độ tin cậy của gợi ý sửa (0.0 đến 1.0)")
    message: Optional[str] = Field(None, description="Mô tả lỗi hoặc cảnh báo")


class QualityResult(BaseModel):
    # --- Existing Legacy Fields (100% Backward Compatible) ---
    is_valid: bool = Field(True, description="Đánh giá hợp lệ trên DevRadar (True khi is_it=True VÀ toxicity='safe')")
    is_it: bool = Field(..., description="Có thuộc lĩnh vực CNTT hay không")
    it_probability: float = Field(..., description="Độ tin cậy lĩnh vực IT")
    toxicity: ToxicityResult = Field(..., description="Kết quả phân tích nội dung độc hại (Legacy format)")
    quality_score: int = Field(..., description="Thang điểm chất lượng (0 - 100)")
    quality_level: str = Field(..., description="Mức chất lượng (excellent, good, average, poor)")
    statistics: ArticleStatistics = Field(..., description="Thống kê các chỉ số bài viết")
    issues: List[QualityIssue] = Field(default_factory=list, description="Danh sách vấn đề phát hiện")
    cleaned_text: Optional[str] = Field(None, description="Văn bản đã qua làm sạch và chuẩn hóa")

    # --- Extended Core AI/ML Fields ---
    content_id: Optional[str] = Field(None, description="ID bài viết")
    user_id: Optional[str] = Field(None, description="ID tác giả")

    it_relevance: Optional[ITRelevanceResult] = Field(None, description="Phân loại chi tiết IT Relevance")
    domain: Optional[ITDomainResult] = Field(None, description="Phân loại chuyên ngành IT cụ thể")
    safety_classification: Optional[SafetyClassification] = Field(None, description="Đánh giá an toàn đa nhãn chi tiết")
    code_analysis: Optional[CodeAnalysisResult] = Field(None, description="Phân tích mã nguồn chuyên sâu")
    semantic: Optional[SemanticResult] = Field(None, description="Metadata vector embedding & semantic clustering")
    suggested_tags: List[str] = Field(default_factory=list, description="Danh sách thẻ công nghệ trích xuất")
    duplicate_analysis: Optional[DuplicateAnalysisResult] = Field(None, description="Phát hiện trùng lặp & đạo văn")
    technical_depth: Optional[TechnicalDepthResult] = Field(None, description="Chỉ số độ sâu kỹ thuật")
    score_breakdown: Optional[Dict[str, float]] = Field(None, description="Bảng phân rã chi tiết thành phần điểm số")
    model_versions: Optional[Dict[str, str]] = Field(None, description="Phiên bản các mô hình ML tham gia xử lý")
    created_at: Optional[str] = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="Thời điểm phân tích")


class HealthCheckResponse(BaseModel):
    status: str
    service: str
    env: str
    components: Dict[str, Any]
