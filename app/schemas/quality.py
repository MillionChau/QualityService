from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    content: str = Field(..., description="Nội dung bài viết cần phân tích và chấm điểm", min_length=1)


class ToxicityResult(BaseModel):
    label: str = Field(..., description="Phân loại: safe, suspicious, toxic")
    probability: float = Field(..., description="Xác suất dự đoán (0.0 đến 1.0)")


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
    is_it: bool = Field(..., description="Có thuộc lĩnh vực CNTT hay không")
    it_probability: float = Field(..., description="Độ tin cậy lĩnh vực IT")
    toxicity: ToxicityResult = Field(..., description="Kết quả phân tích nội dung độc hại")
    quality_score: int = Field(..., description="Thang điểm chất lượng (0 - 100)")
    quality_level: str = Field(..., description="Mức chất lượng (excellent, good, average, poor)")
    statistics: ArticleStatistics = Field(..., description="Thống kê các chỉ số bài viết")
    issues: List[QualityIssue] = Field(default_factory=list, description="Danh sách vấn đề phát hiện")
    cleaned_text: Optional[str] = Field(None, description="Văn bản đã qua làm sạch và chuẩn hóa")


class HealthCheckResponse(BaseModel):
    status: str
    service: str
    env: str
    components: Dict[str, Any]
