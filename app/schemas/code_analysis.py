from typing import List, Optional
from pydantic import BaseModel, Field


class CodeAnalysisResult(BaseModel):
    has_code: bool = Field(False, description="Có chứa mã nguồn hay không")
    code_blocks_count: int = Field(0, description="Số lượng khối code block (```...```)")
    inline_code_count: int = Field(0, description="Số lượng inline code (`...`)")
    declared_languages: List[str] = Field(default_factory=list, description="Các ngôn ngữ lập trình được khai báo trong code block")
    detected_languages: List[str] = Field(default_factory=list, description="Các ngôn ngữ lập trình được nhận diện tự động")
    code_ratio: float = Field(0.0, ge=0.0, le=1.0, description="Tỷ lệ ký tự code trên tổng số ký tự bài viết")
    technical_terms_count: int = Field(0, description="Số lượng thuật ngữ công nghệ trong bài")
