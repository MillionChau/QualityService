from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DuplicateType(str, Enum):
    EXACT_DUPLICATE = "exact_duplicate"
    NEAR_DUPLICATE = "near_duplicate"
    SEMANTICALLY_SIMILAR = "semantically_similar"
    ORIGINAL = "original"


class SemanticResult(BaseModel):
    embedding_model: str = Field("devradar-embedding-v1", description="Tên model tạo vector embedding")
    vector_dimension: int = Field(768, description="Số chiều vector embedding")
    cluster_id: Optional[str] = Field(None, description="Mã cụm chủ đề semantic (Cluster ID)")
    cluster_name: Optional[str] = Field(None, description="Tên cụm chủ đề semantic")
    embedding_vector: Optional[List[float]] = Field(None, description="Mảng vector dense embedding (Optional)")


class DuplicateAnalysisResult(BaseModel):
    is_duplicate: bool = Field(False, description="Có bị nghi ngờ trùng lặp/đạo văn hay không")
    duplicate_type: DuplicateType = Field(DuplicateType.ORIGINAL, description="Phân loại mức độ trùng lặp")
    lexical_similarity: float = Field(0.0, ge=0.0, le=1.0, description="Độ tương đồng từ vựng (MinHash/SimHash/Jaccard)")
    semantic_similarity: float = Field(0.0, ge=0.0, le=1.0, description="Độ tương đồng ngữ nghĩa (Cosine Similarity)")
    highest_similarity_score: float = Field(0.0, ge=0.0, le=1.0, description="Điểm tương đồng cao nhất")
    matched_content_id: Optional[str] = Field(None, description="ID bài viết bị trùng lặp nhất")
    matched_content_title: Optional[str] = Field(None, description="Tiêu đề bài viết bị trùng lặp nhất")


class SimilarityQueryRequest(BaseModel):
    content_id: Optional[str] = Field(None, description="ID bài viết để so sánh")
    content: Optional[str] = Field(None, description="Văn bản cần so sánh độ tương đồng")
    top_k: int = Field(5, ge=1, le=50, description="Số lượng kết quả tương đồng nhất cần lấy")
    threshold: float = Field(0.70, ge=0.0, le=1.0, description="Ngưỡng tương đồng tối thiểu")


class SimilaritySearchResult(BaseModel):
    content_id: str = Field(..., description="ID bài viết khớp")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Điểm tương đồng")
    duplicate_type: DuplicateType = Field(DuplicateType.SEMANTICALLY_SIMILAR)
    title: Optional[str] = Field(None, description="Tiêu đề bài viết")
