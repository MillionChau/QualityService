from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class UserRankEnum(str, Enum):
    NEWCOMER = "Newcomer"                  # 0–99
    CONTRIBUTOR = "Contributor"            # 100–249
    DEVELOPER = "Developer"                # 250–449
    EXPERT = "Expert"                      # 450–649
    SENIOR = "Senior"                      # 650–799
    MENTOR = "Mentor"                      # 800–899
    COMMUNITY_LEADER = "Community Leader"  # 900–1000


class UserFeatureVector(BaseModel):
    content_quality: float = Field(0.5, ge=0.0, le=1.0, description="Chất lượng nội dung trung bình/trọng số")
    technical_contribution: float = Field(0.0, ge=0.0, le=1.0, description="Đóng góp bài viết kỹ thuật chuyên sâu")
    helpfulness: float = Field(0.0, ge=0.0, le=1.0, description="Độ hữu ích dựa trên vote/chấp nhận câu trả lời")
    community_trust: float = Field(0.5, ge=0.0, le=1.0, description="Độ tin cậy từ cộng đồng")
    consistency: float = Field(0.0, ge=0.0, le=1.0, description="Độ đều đặn hoạt động đóng góp")
    activity: float = Field(0.0, ge=0.0, le=1.0, description="Mức độ hoạt động (Rolling window 30/90 ngày)")
    toxicity_rate: float = Field(0.0, ge=0.0, le=1.0, description="Tỷ lệ vi phạm độc hại")
    spam_rate: float = Field(0.0, ge=0.0, le=1.0, description="Tỷ lệ rác/spam")
    moderation_penalty: float = Field(0.0, ge=0.0, le=1.0, description="Điểm phạt xử lý vi phạm")


class UserScoreBreakdown(BaseModel):
    content_quality_score: float = Field(0.0, description="Đóng góp từ chất lượng nội dung")
    technical_contribution_score: float = Field(0.0, description="Đóng góp từ giá trị kỹ thuật")
    helpfulness_score: float = Field(0.0, description="Đóng góp từ độ hữu ích")
    community_trust_score: float = Field(0.0, description="Đóng góp từ niềm tin cộng đồng")
    consistency_score: float = Field(0.0, description="Đóng góp từ sự kiên trì")
    activity_score: float = Field(0.0, description="Đóng góp từ tần suất hoạt động")
    applied_penalties: Dict[str, float] = Field(default_factory=dict, description="Các hình phạt anti-gaming & moderation")


class PromotionEligibility(BaseModel):
    eligible: bool = Field(False, description="Liệu user có đủ điều kiện nâng cấp Rank tiếp theo hay không")
    current_level: UserRankEnum = Field(UserRankEnum.NEWCOMER, description="Hạng hiện tại")
    next_level: Optional[UserRankEnum] = Field(UserRankEnum.CONTRIBUTOR, description="Hạng tiếp theo")
    missing_requirements: List[str] = Field(default_factory=list, description="Danh sách các điều kiện còn thiếu để được thăng hạng")
    explanation: Optional[str] = Field(None, description="Giải thích chi tiết về quyết định thăng hạng")


class UserReputationResult(BaseModel):
    user_id: str = Field(..., description="Mã người dùng")
    user_score: int = Field(0, ge=0, le=1000, description="Điểm uy tín tổng hợp (0 - 1000)")
    rank: UserRankEnum = Field(UserRankEnum.NEWCOMER, description="Danh hiệu / Hạng người dùng")
    features: UserFeatureVector = Field(default_factory=UserFeatureVector, description="Vector đặc trưng người dùng")
    breakdown: UserScoreBreakdown = Field(default_factory=UserScoreBreakdown, description="Bảng giải thích đóng góp điểm số")
    promotion: PromotionEligibility = Field(default_factory=PromotionEligibility, description="Thông tin xét duyệt thăng hạng")
