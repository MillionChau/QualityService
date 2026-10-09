from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import re

router = APIRouter(prefix="/api/v1/ai", tags=["AI Assistant"])

class ChatMessage(BaseModel):
    role: str # user, assistant, system
    content: str

class ChatRequest(BaseModel):
    question: str
    history: Optional[List[ChatMessage]] = []
    context: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    suggested_topics: List[str]

class SummarizeRequest(BaseModel):
    content: str
    max_length: Optional[int] = 200

class SummarizeResponse(BaseModel):
    summary: str
    key_points: List[str]

@router.post("/chat", response_model=ChatResponse)
async def ai_chat(req: ChatRequest):
    """
    UC-58: Trợ lý AI Hỏi - Đáp kỹ thuật lập trình và kiến trúc hệ thống.
    Hỗ trợ sinh câu trả lời tư vấn lập trình, gợi ý giải pháp kỹ thuật và chủ đề liên quan.
    """
    q = req.question.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Câu hỏi không được để trống")
    
    # Trả lời phân tích dựa trên ngữ cảnh lập trình (Fallback intelligent heuristic & engine template)
    q_lower = q.lower()
    answer_parts = []
    suggested = ["Clean Architecture", "Microservices Design", "Docker & Kubernetes", "CI/CD Pipeline"]

    if "docker" in q_lower or "container" in q_lower:
        answer_parts.append("Về Docker & Containerization: Bạn nên chia nhỏ Dockerfile thành multi-stage build để giảm kích thước image. Đảm bảo cấu hình .dockerignore và không chạy container dưới quyền root.")
        suggested = ["Docker Multi-stage", "Kubernetes Pod Deployment", "Docker Compose Local Dev"]
    elif "microservice" in q_lower or "architecture" in q_lower:
        answer_parts.append("Về Kiến trúc Microservices: Đảm bảo phân định rõ Boundary Context giữa các domain. Giao tiếp giữa các service nên kết hợp HTTP/REST cho synchronous query và Message Broker (RabbitMQ/Kafka) cho asynchronous events nhằm đạt tính decoupling cao.")
        suggested = ["Event-Driven Architecture", "API Gateway Pattern", "Distributed Tracing"]
    elif "sql" in q_lower or "database" in q_lower:
        answer_parts.append("Về Cơ sở dữ liệu: Hãy đảm bảo index phù hợp cho các trường thường xuyên filter/sort, tối ưu query N+1, và tách biệt connection read/write nếu lưu lượng truy cập cao.")
        suggested = ["Database Indexing", "Query Optimization", "Sharding & Replication"]
    else:
        answer_parts.append(f"DevRadar AI Assistant đã ghi nhận câu hỏi kỹ thuật của bạn: '{q}'. Đối với vấn đề này, giải pháp khuyến nghị là áp dụng các best practices về Clean Code, cấu trúc rõ ràng các tầng Domain/Application/Infrastructure, và viết unit test bao phủ các ca biên (edge cases).")

    return ChatResponse(
        answer="\n\n".join(answer_parts),
        suggested_topics=suggested
    )

@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_post(req: SummarizeRequest):
    """
    UC-60: Tóm tắt bài viết kỹ thuật tự động bằng AI.
    Trích xuất nội dung cốt lõi và các điểm chính từ bài viết của lập trình viên.
    """
    text = req.content.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Nội dung bài viết không được để trống")
    
    # Split text into sentences
    sentences = [s.strip() for s in re.split(r'[.\n!?]+', text) if len(s.strip()) > 15]
    
    if not sentences:
        summary = text[:req.max_length]
        key_points = [text[:50]]
    else:
        summary = ". ".join(sentences[:2]) + "."
        if len(summary) > (req.max_length or 200):
            summary = summary[:req.max_length] + "..."
        
        key_points = sentences[:3]

    return SummarizeResponse(
        summary=summary,
        key_points=key_points
    )
