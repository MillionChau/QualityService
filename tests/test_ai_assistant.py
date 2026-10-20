import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.clients.llm_client import LLMClient
from app.services.ai_fallback_engine import ai_fallback_engine

client = TestClient(app)


# =============================================================================
# 1. Tests for AIFallbackEngine (Task 1.15)
# =============================================================================

def test_fallback_explain_developer_radar():
    metrics = {
        "Coding": 85.0,
        "Architecture": 75.0,
        "Review": 65.0,
        "Community": 50.0,
        "Consistency": 80.0
    }
    res = ai_fallback_engine.explain_dashboard("developer_radar", metrics, {"username": "alice_dev"})
    assert res["chart_type"] == "developer_radar"
    assert "alice_dev" in res["summary"]
    assert len(res["strengths"]) >= 1
    assert any("Coding" in s for s in res["strengths"])
    assert len(res["improvements"]) >= 1
    assert any("Community" in imp for imp in res["improvements"])
    assert len(res["recommendations"]) >= 2
    assert res["provider"] == "heuristic_fallback"


def test_fallback_explain_repo_health():
    metrics = {
        "health_score": 88.5,
        "commit_count": 25,
        "pr_count": 5
    }
    res = ai_fallback_engine.explain_dashboard("repo_health", metrics, {"repo_name": "DevRadar/Core"})
    assert res["chart_type"] == "repo_health"
    assert "DevRadar/Core" in res["summary"]
    assert "88.5" in res["summary"]
    assert len(res["strengths"]) >= 1
    assert len(res["recommendations"]) >= 2


def test_fallback_explain_tech_trend():
    metrics = {
        "growth_rate": 35.0,
        "star_velocity": 12.0
    }
    res = ai_fallback_engine.explain_dashboard("tech_trend", metrics, {"name": "FastAPI"})
    assert res["chart_type"] == "tech_trend"
    assert "FastAPI" in res["summary"]
    assert len(res["strengths"]) >= 1


def test_fallback_chat():
    res = ai_fallback_engine.chat_fallback("Làm thế nào để tối ưu Dockerfile?")
    assert "Docker" in res["answer"]
    assert len(res["suggested_topics"]) >= 2

    res_clean = ai_fallback_engine.chat_fallback("Kiến trúc Clean Architecture gồm những tầng nào?")
    assert "Clean Architecture" in res_clean["answer"]


def test_fallback_summarize():
    content = (
        "Microservices là một kiến trúc phần mềm phổ biến trong các hệ thống phân tán lớn. "
        "Mỗi dịch vụ sẽ chịu trách nhiệm cho một domain độc lập và giao tiếp qua API hoặc Message Broker. "
        "Để đảm bảo hệ thống vận hành ổn định, cần có giải pháp Distributed Tracing và Centralized Logging."
    )
    res = ai_fallback_engine.summarize_fallback(content, max_length=150)
    assert len(res["summary"]) > 0
    assert len(res["key_points"]) >= 1


# =============================================================================
# 2. Tests for LLMClient (Task 1.10)
# =============================================================================

@pytest.mark.asyncio
async def test_llm_client_disabled_returns_none():
    client_instance = LLMClient()
    client_instance.enabled = False
    result = await client_instance.chat_completion([{"role": "user", "content": "hi"}])
    assert result is None


@pytest.mark.asyncio
async def test_llm_client_handles_timeout_gracefully():
    client_instance = LLMClient()
    client_instance.enabled = True
    client_instance.api_key = "dummy_key"

    with patch("httpx.AsyncClient.post", side_effect=Exception("Connection timeout")):
        result = await client_instance.chat_completion([{"role": "user", "content": "hi"}])
        assert result is None


# =============================================================================
# 3. Tests for API Endpoints (Task 1.12, 1.13, 1.14)
# =============================================================================

def test_api_chat_with_mock_llm():
    mock_reply = (
        "Clean Architecture giúp tách biệt business logic khỏi framework.\n\n"
        "SUGGESTED_TOPICS: Domain-Driven Design, MediatR CQRS, Unit Testing"
    )

    with patch("app.clients.llm_client.llm_client.chat_completion", new=AsyncMock(return_value=mock_reply)):
        resp = client.post("/api/v1/ai/chat", json={
            "question": "Lợi ích của Clean Architecture?",
            "history": []
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "Clean Architecture" in data["answer"]
        assert "SUGGESTED_TOPICS:" not in data["answer"]
        assert "Domain-Driven Design" in data["suggested_topics"]
        assert "external_llm" in data["provider"]


def test_api_chat_fallback_when_llm_fails():
    with patch("app.clients.llm_client.llm_client.chat_completion", new=AsyncMock(return_value=None)):
        resp = client.post("/api/v1/ai/chat", json={
            "question": "Docker container là gì?"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "Docker" in data["answer"]
        assert data["provider"] == "heuristic_fallback"


def test_api_summarize_with_mock_llm():
    mock_json = '{"summary": "FastAPI là framework hiệu năng cao.", "key_points": ["Tốc độ cao", "Dễ viết", "Tự sinh Swagger"]}'

    with patch("app.clients.llm_client.llm_client.generate_text", new=AsyncMock(return_value=mock_json)):
        resp = client.post("/api/v1/ai/summarize", json={
            "content": "FastAPI là một web framework hiện đại, có tốc độ rất cao dành cho Python.",
            "max_length": 200
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "FastAPI" in data["summary"]
        assert len(data["key_points"]) == 3
        assert "external_llm" in data["provider"]


def test_api_summarize_fallback_when_llm_fails():
    with patch("app.clients.llm_client.llm_client.generate_text", new=AsyncMock(return_value=None)):
        resp = client.post("/api/v1/ai/summarize", json={
            "content": "Microservices giúp chia nhỏ kiến trúc monolith. Mỗi service quản lý một database riêng biệt.",
            "max_length": 150
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["summary"]) > 0
        assert data["provider"] == "heuristic_fallback"


def test_api_explain_dashboard_radar_mock_llm():
    mock_json = (
        '{"summary": "Hồ sơ kỹ sư rất xuất sắc ở mảng coding.", '
        '"strengths": ["Khả năng coding tốt", "Tính kiên trì cao"], '
        '"improvements": ["Ít review code chéo"], '
        '"recommendations": ["Nên tham gia review PR nhiều hơn"]}'
    )

    with patch("app.clients.llm_client.llm_client.generate_text", new=AsyncMock(return_value=mock_json)):
        resp = client.post("/api/v1/ai/explain-dashboard", json={
            "chart_type": "developer_radar",
            "metrics": {"Coding": 90, "Review": 55, "Consistency": 85},
            "context": {"username": "bob_coder"}
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["chart_type"] == "developer_radar"
        assert "coding" in data["summary"].lower()
        assert len(data["strengths"]) == 2
        assert "external_llm" in data["provider"]


def test_api_explain_dashboard_fallback():
    with patch("app.clients.llm_client.llm_client.generate_text", new=AsyncMock(return_value=None)):
        resp = client.post("/api/v1/ai/explain-dashboard", json={
            "chart_type": "repo_health",
            "metrics": {"health_score": 92.0, "commit_count": 30},
            "context": {"repo_name": "DevRadar/Backend"}
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["chart_type"] == "repo_health"
        assert "DevRadar/Backend" in data["summary"]
        assert data["provider"] == "heuristic_fallback"
