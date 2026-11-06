import json
import re
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logging import logger
from app.clients.llm_client import llm_client
from app.services.ai_fallback_engine import ai_fallback_engine

router = APIRouter(prefix="/api/v1/ai", tags=["AI Assistant"])


# =============================================================================
# Schemas
# =============================================================================

class ChatMessage(BaseModel):
    role: str = Field(..., description="Vai trò: user, assistant, system")
    content: str = Field(..., description="Nội dung tin nhắn")


class ChatRequest(BaseModel):
    question: str = Field(..., description="Câu hỏi kỹ thuật của lập trình viên")
    history: Optional[List[ChatMessage]] = Field(default_factory=list, description="Lịch sử đối thoại trước đó")
    context: Optional[str] = Field(None, description="Ngữ cảnh kỹ thuật bổ trợ (công nghệ, mã lỗi, v.v.)")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Câu trả lời tư vấn kỹ thuật từ AI")
    suggested_topics: List[str] = Field(default_factory=list, description="Các chủ đề kỹ thuật liên quan nên tìm hiểu")
    provider: str = Field(..., description="Nguồn sinh nội dung: external_llm hoặc heuristic_fallback")


class SummarizeRequest(BaseModel):
    content: str = Field(..., description="Nội dung bài viết kỹ thuật cần tóm tắt")
    max_length: Optional[int] = Field(250, description="Độ dài tối đa mong muốn cho đoạn tóm tắt")


class SummarizeResponse(BaseModel):
    summary: str = Field(..., description="Đoạn văn tóm tắt nội dung cốt lõi")
    key_points: List[str] = Field(default_factory=list, description="Danh sách 3-5 luận điểm kỹ thuật quan trọng")
    provider: str = Field(..., description="Nguồn sinh nội dung: external_llm hoặc heuristic_fallback")


class ExplainDashboardRequest(BaseModel):
    chart_type: str = Field(..., description="Loại biểu đồ: developer_radar, repo_health, tech_trend, language_health")
    metrics: Dict[str, Any] = Field(..., description="Chỉ số/giá trị các trục của biểu đồ")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Ngữ cảnh: username, repo_name, period, role")


class ExplainDashboardResponse(BaseModel):
    chart_type: str = Field(..., description="Loại biểu đồ phân tích")
    summary: str = Field(..., description="Nhận định tổng quan (Executive Summary)")
    strengths: List[str] = Field(default_factory=list, description="Điểm mạnh nổi bật")
    improvements: List[str] = Field(default_factory=list, description="Điểm rủi ro / Cần cải thiện")
    recommendations: List[str] = Field(default_factory=list, description="Lời khuyên hành động thực tế")
    provider: str = Field(..., description="Nguồn sinh nội dung: external_llm hoặc heuristic_fallback")


# =============================================================================
# Helper function to extract JSON from LLM output
# =============================================================================

def _extract_json_from_llm(raw: str) -> Optional[Dict[str, Any]]:
    """Trích xuất dictionary từ chuỗi phản hồi LLM (kể cả khi bọc trong markdown code fence)."""
    if not raw:
        return None
    cleaned = raw.strip()
    # Tìm khối ```json ... ``` hoặc ``` ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
    if match:
        cleaned = match.group(1).strip()
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except Exception:
        # Thử tìm substring từ ký tự { đầu tiên đến } cuối cùng
        first_brace = cleaned.find("{")
        last_brace = cleaned.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            try:
                data = json.loads(cleaned[first_brace:last_brace + 1])
                if isinstance(data, dict):
                    return data
            except Exception:
                pass
    return None


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/ai-status", summary="Kiểm tra trạng thái cấu hình AI & UnoRouter LLM")
@router.get("/status", summary="Kiểm tra trạng thái cấu hình AI & UnoRouter LLM")
async def ai_status():
    return {
        "external_ai_enabled": settings.EXTERNAL_AI_ENABLED,
        "ai_model": settings.AI_MODEL,
        "ai_base_url": settings.AI_BASE_URL,
        "is_available": llm_client.is_available(),
        "has_api_key": bool(settings.AI_API_KEY)
    }


@router.post("/chat", response_model=ChatResponse, summary="UC-44: Trợ lý AI Hỏi - Đáp kỹ thuật lập trình")
async def ai_chat(req: ChatRequest):
    """
    UC-44: Trợ lý AI Hỏi - Đáp chuyên sâu về kỹ thuật lập trình và kiến trúc hệ thống.
    Kết hợp mô hình LLM qua UnoRouter Gateway với tầng Heuristic Fallback an toàn.
    """
    q = req.question.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Câu hỏi không được để trống")

    provider_name = f"external_llm:{settings.AI_MODEL}"

    # 1. Thử gọi External LLM qua UnoRouter Gateway
    if llm_client.is_available():
        system_prompt = (
            "Bạn là Chuyên gia Tư vấn Kỹ thuật Cấp cao (Senior Software Architect & Tech Lead) của nền tảng DevRadar. "
            "Nhiệm vụ của bạn là giải đáp chuyên sâu, chuẩn mực về các chủ đề: Clean Architecture, Microservices, "
            "CQRS, Design Patterns, Docker, Kubernetes, CI/CD, tối ưu Cơ sở dữ liệu (PostgreSQL, MongoDB, Redis), "
            "lập trình C#/.NET, Python, giải thích lỗi code rõ ràng kèm ví dụ mã ngắn gọn khi cần thiết. "
            "Cuối câu trả lời, hãy LUÔN LUÔN ghi 1 dòng gợi ý 3-4 chủ đề liên quan theo đúng định dạng sau:\n"
            "SUGGESTED_TOPICS: Chủ đề 1, Chủ đề 2, Chủ đề 3"
        )

        messages = [{"role": "system", "content": system_prompt}]
        if req.context:
            messages.append({"role": "system", "content": f"Ngữ cảnh bổ trợ: {req.context}"})

        # Bổ sung tối đa 6 lượt hội thoại gần nhất
        if req.history:
            for item in req.history[-6:]:
                messages.append({"role": item.role, "content": item.content})

        messages.append({"role": "user", "content": q})

        llm_reply = await llm_client.chat_completion(messages, temperature=0.7, max_tokens=1500)
        if llm_reply:
            answer = llm_reply.strip()
            suggested_topics = []

            # Tách SUGGESTED_TOPICS ở cuối
            match = re.search(r"SUGGESTED_TOPICS:\s*(.*)$", answer, re.IGNORECASE)
            if match:
                raw_topics = match.group(1).strip()
                suggested_topics = [t.strip() for t in raw_topics.split(",") if t.strip()]
                # Cắt bỏ dòng SUGGESTED_TOPICS khỏi câu trả lời chính
                answer = answer[:match.start()].strip()

            if not suggested_topics:
                suggested_topics = ["Clean Architecture", "Microservices Design", "Docker & Kubernetes", "CI/CD Pipeline"]

            return ChatResponse(
                answer=answer,
                suggested_topics=suggested_topics[:4],
                provider=provider_name
            )

    # 2. Graceful Fallback Engine (khi LLM offline, timeout hoặc chưa cấu hình)
    logger.info("Executing Heuristic Fallback Engine for AI Chat...")
    fallback_res = ai_fallback_engine.chat_fallback(q)
    return ChatResponse(
        answer=fallback_res["answer"],
        suggested_topics=fallback_res["suggested_topics"],
        provider="heuristic_fallback"
    )


@router.post("/summarize", response_model=SummarizeResponse, summary="UC-46: Tóm tắt bài viết kỹ thuật chuyên sâu bằng AI")
async def summarize_post(req: SummarizeRequest):
    """
    UC-46: Tóm tắt bài viết kỹ thuật tự động bằng LLM.
    Trích xuất đoạn tóm tắt cốt lõi (100-200 từ) và danh sách 3-5 luận điểm kiến thức quan trọng.
    """
    text = req.content.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Nội dung bài viết không được để trống")

    max_len = req.max_length or 250
    provider_name = f"external_llm:{settings.AI_MODEL}"

    # 1. Thử gọi External LLM qua UnoRouter
    if llm_client.is_available():
        system_prompt = (
            "Bạn là chuyên gia biên tập và tóm tắt tài liệu công nghệ của DevRadar. "
            "Nhiệm vụ của bạn là đọc bài viết kỹ thuật được cung cấp và trích xuất:\n"
            f"1. Một đoạn tóm tắt nội dung cốt lõi súc tích, mạch lạc bằng tiếng Việt (tối đa {max_len} ký tự).\n"
            "2. Danh sách 3-5 gạch đầu dòng các luận điểm/kiến thức kỹ thuật quan trọng nhất.\n\n"
            "BẮT BUỘC chỉ trả về kết quả theo cấu trúc JSON chuẩn sau, không thêm lời dẫn hay ký tự thừa:\n"
            "{\n"
            '  "summary": "Đoạn văn tóm tắt bài viết...",\n'
            '  "key_points": ["Luận điểm 1", "Luận điểm 2", "Luận điểm 3"]\n'
            "}"
        )

        raw_llm = await llm_client.generate_text(system_prompt, text, temperature=0.3, max_tokens=1000)
        parsed = _extract_json_from_llm(raw_llm) if raw_llm else None

        if parsed and "summary" in parsed:
            summary = str(parsed.get("summary", "")).strip()
            key_points = parsed.get("key_points", [])
            if not isinstance(key_points, list):
                key_points = [str(key_points)]

            return SummarizeResponse(
                summary=summary,
                key_points=[str(kp) for kp in key_points if kp],
                provider=provider_name
            )

    # 2. Fallback Heuristic
    logger.info("Executing Heuristic Fallback Engine for AI Summarize...")
    fallback_res = ai_fallback_engine.summarize_fallback(text, max_length=max_len)
    return SummarizeResponse(
        summary=fallback_res["summary"],
        key_points=fallback_res["key_points"],
        provider="heuristic_fallback"
    )


@router.post("/explain-dashboard", response_model=ExplainDashboardResponse, summary="UC-45: AI Giải thích Biểu đồ Dashboard & Radar năng lực")
async def explain_dashboard(req: ExplainDashboardRequest):
    """
    UC-45: Phân tích biểu đồ (Developer Radar 5 trục, Repository Health, Tech Trend, Language Health).
    Sinh lời bình luận và khuyến nghị 4 phần:
    1. Nhận định tổng quan (Executive Summary).
    2. Điểm mạnh nổi bật (Strengths).
    3. Điểm rủi ro / Cần cải thiện (Improvements).
    4. Lời khuyên hành động thực tế (Recommendations).
    """
    if not req.chart_type or not req.chart_type.strip():
        raise HTTPException(status_code=400, detail="Loại biểu đồ (chart_type) không được để trống")

    provider_name = f"external_llm:{settings.AI_MODEL}"

    # 1. Thử gọi External LLM qua UnoRouter
    if llm_client.is_available():
        system_prompt = (
            "Bạn là Chuyên gia Đánh giá Năng lực Kỹ sư & Cố vấn Dữ liệu (Engineering Analytics Advisor) của nền tảng DevRadar. "
            "Nhiệm vụ của bạn là đọc các chỉ số biểu đồ kỹ thuật và phân tích thành 4 phần rõ ràng:\n"
            "1. Nhận định tổng quan (summary): Đánh giá 2-3 câu súc tích về tình trạng chung.\n"
            "2. Điểm mạnh nổi bật (strengths): 2-3 gạch đầu dòng về các chỉ số xuất sắc.\n"
            "3. Điểm rủi ro / Cần cải thiện (improvements): 2-3 gạch đầu dòng về các khía cạnh còn yếu.\n"
            "4. Lời khuyên hành động thực tế (recommendations): 2-3 khuyến nghị kỹ thuật cụ thể, khả thi.\n\n"
            "BẮT BUỘC chỉ trả về kết quả bằng JSON chuẩn sau, không thêm bất kỳ văn bản nào bên ngoài:\n"
            "{\n"
            '  "summary": "...",\n'
            '  "strengths": ["...", "..."],\n'
            '  "improvements": ["...", "..."],\n'
            '  "recommendations": ["...", "..."]\n'
            "}"
        )

        user_content = (
            f"Loại biểu đồ: {req.chart_type}\n"
            f"Các chỉ số phân tích: {json.dumps(req.metrics, ensure_ascii=False)}\n"
            f"Ngữ cảnh đối tượng: {json.dumps(req.context or {}, ensure_ascii=False)}"
        )

        raw_llm = await llm_client.generate_text(system_prompt, user_content, temperature=0.4, max_tokens=1200)
        parsed = _extract_json_from_llm(raw_llm) if raw_llm else None

        if parsed and "summary" in parsed:
            return ExplainDashboardResponse(
                chart_type=req.chart_type,
                summary=str(parsed.get("summary", "")).strip(),
                strengths=[str(s) for s in parsed.get("strengths", []) if s],
                improvements=[str(i) for i in parsed.get("improvements", []) if i],
                recommendations=[str(r) for r in parsed.get("recommendations", []) if r],
                provider=provider_name
            )

    # 2. Fallback Heuristic
    logger.info("Executing Heuristic Fallback Engine for Explain Dashboard...")
    fallback_res = ai_fallback_engine.explain_dashboard(req.chart_type, req.metrics, req.context)
    return ExplainDashboardResponse(
        chart_type=fallback_res.get("chart_type", req.chart_type),
        summary=fallback_res.get("summary", ""),
        strengths=fallback_res.get("strengths", []),
        improvements=fallback_res.get("improvements", []),
        recommendations=fallback_res.get("recommendations", []),
        provider="heuristic_fallback"
    )
