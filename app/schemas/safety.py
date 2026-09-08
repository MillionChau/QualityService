from typing import Dict, Optional
from pydantic import BaseModel, Field


class SafetyScores(BaseModel):
    safe: float = Field(1.0, ge=0.0, le=1.0, description="Xác suất nội dung an toàn")
    toxic: float = Field(0.0, ge=0.0, le=1.0, description="Xác suất nội dung độc hại nói chung")
    suspicious: float = Field(0.0, ge=0.0, le=1.0, description="Xác suất nghi vấn")
    spam: float = Field(0.0, ge=0.0, le=1.0, description="Xác suất rác/quảng cáo")
    harassment: float = Field(0.0, ge=0.0, le=1.0, description="Xác suất xúc phạm/quấy rối")
    hate: float = Field(0.0, ge=0.0, le=1.0, description="Xác suất thù ghét/kích động")
    sexual: float = Field(0.0, ge=0.0, le=1.0, description="Xác suất nội dung nhạy cảm")
    violent: float = Field(0.0, ge=0.0, le=1.0, description="Xác suất bạo lực")
    scam: float = Field(0.0, ge=0.0, le=1.0, description="Xác suất lừa đảo/mã độc")


class SafetyClassification(BaseModel):
    primary_label: str = Field("safe", description="Nhãn chính: safe, suspicious, toxic, spam, harassment, hate, sexual, violent, scam")
    probability: float = Field(1.0, ge=0.0, le=1.0, description="Độ tin cậy của nhãn chính")
    scores: SafetyScores = Field(default_factory=SafetyScores, description="Chi tiết xác suất từng loại nội dung")
    is_acceptable: bool = Field(True, description="Liệu nội dung có đạt tiêu chuẩn an toàn để xuất bản")


class ToxicityResult(BaseModel):
    """Legacy compatibility model for existing API contract."""
    label: str = Field(..., description="Phân loại: safe, suspicious, toxic")
    probability: float = Field(..., description="Xác suất dự đoán (0.0 đến 1.0)")
