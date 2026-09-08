from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class DatasetSample(BaseModel):
    text: str = Field(..., description="Văn bản mẫu bài viết")
    language: str = Field("vi", description="Mã ngôn ngữ: vi, en, mixed")
    is_it: bool = Field(True, description="Nhãn lĩnh vực IT")
    domain: Optional[str] = Field(None, description="Nhãn chuyên ngành IT")
    safety_labels: Dict[str, bool] = Field(
        default_factory=lambda: {"safe": True, "toxic": False, "spam": False},
        description="Bộ nhãn đa tiêu chí an toàn"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata bổ sung (tỷ lệ code, nguồn bài viết,...)")


class ModelMetrics(BaseModel):
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1: Optional[float] = None
    macro_f1: Optional[float] = None
    confusion_matrix: Optional[List[List[int]]] = None
    custom_metrics: Dict[str, float] = Field(default_factory=dict)


class ModelMetadata(BaseModel):
    model_name: str = Field(..., description="Tên mô hình ML")
    version: str = Field(..., description="Phiên bản mô hình (ví dụ: v1.0.0)")
    training_dataset_version: str = Field(..., description="Phiên bản dataset được dùng để huấn luyện")
    training_date: Optional[str] = Field(None, description="Thời gian huấn luyện")
    framework_version: Optional[str] = Field(None, description="Phiên bản framework (scikit-learn, fasttext, transformers, torch)")
    tokenizer_version: Optional[str] = Field(None, description="Phiên bản tokenizer tương ứng")
    metrics: ModelMetrics = Field(default_factory=ModelMetrics, description="Các chỉ số đánh giá model")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Siêu tham số huấn luyện (Hyperparameters)")
