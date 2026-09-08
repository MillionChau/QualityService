from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ITRelevanceLabel(str, Enum):
    IT = "IT"
    NON_IT = "NON_IT"
    UNCERTAIN = "UNCERTAIN"


class ITDomainLabel(str, Enum):
    PROGRAMMING = "PROGRAMMING"
    BACKEND = "BACKEND"
    FRONTEND = "FRONTEND"
    MOBILE = "MOBILE"
    DEVOPS = "DEVOPS"
    CLOUD = "CLOUD"
    DATABASE = "DATABASE"
    AI_ML = "AI_ML"
    DATA_ENGINEERING = "DATA_ENGINEERING"
    CYBERSECURITY = "CYBERSECURITY"
    SOFTWARE_ARCHITECTURE = "SOFTWARE_ARCHITECTURE"
    TESTING = "TESTING"
    EMBEDDED = "EMBEDDED"
    NETWORKING = "NETWORKING"
    OTHER_IT = "OTHER_IT"
    UNKNOWN = "UNKNOWN"


class ITRelevanceResult(BaseModel):
    label: ITRelevanceLabel = Field(ITRelevanceLabel.IT, description="Nhãn phân loại IT: IT, NON_IT, UNCERTAIN")
    probability: float = Field(..., ge=0.0, le=1.0, description="Xác suất bài viết thuộc CNTT")
    is_it: bool = Field(True, description="Flag Boolean quyết định IT hay không")


class ITDomainResult(BaseModel):
    label: ITDomainLabel = Field(ITDomainLabel.UNKNOWN, description="Chuyên ngành IT cụ thể")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Độ tin cậy dự đoán chuyên ngành")
    secondary_label: Optional[ITDomainLabel] = Field(None, description="Chuyên ngành phụ nếu có")
