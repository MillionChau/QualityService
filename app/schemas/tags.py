from typing import List, Optional
from pydantic import BaseModel, Field


class TagExtractionItem(BaseModel):
    tag_name: str = Field(..., description="Tên thẻ công nghệ (vd: FastAPI, Docker, Python)")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Độ tin cậy của gợi ý tag")
    source: str = Field("semantic_dictionary", description="Nguồn trích xuất: semantic_model, dictionary, code_detection")
    category: Optional[str] = Field(None, description="Danh mục công nghệ: framework, language, devops, database, tool")


class TagExtractionResult(BaseModel):
    suggested_tags: List[str] = Field(default_factory=list, description="Danh sách tên các tag công nghệ được trích xuất")
    details: List[TagExtractionItem] = Field(default_factory=list, description="Chi tiết độ tin cậy và nguồn trích xuất của từng tag")
