from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TechnicalDepthResult(BaseModel):
    score: float = Field(0.5, ge=0.0, le=1.0, description="Điểm độ sâu kỹ thuật (0.0 đến 1.0)")
    terminology_density: float = Field(0.0, ge=0.0, le=1.0, description="Mật độ sử dụng thuật ngữ chuyên môn")
    specificity_score: float = Field(0.0, ge=0.0, le=1.0, description="Độ cụ thể của bài viết (ví dụ cụ thể, thông số, phiên bản)")
    explanation_quality: float = Field(0.0, ge=0.0, le=1.0, description="Chất lượng diễn giải vấn đề & giải pháp")
    coherence_score: float = Field(0.0, ge=0.0, le=1.0, description="Độ mạch lạc ngữ nghĩa giữa các câu đoạn")
    signals: List[str] = Field(default_factory=list, description="Các tín hiệu kỹ thuật phát hiện được")
