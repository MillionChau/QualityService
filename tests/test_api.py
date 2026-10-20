import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/api/v1/quality/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "components" in data


def test_analyze_endpoint():
    payload = {
        "content": "<h1>Học Python FastAPI</h1><p>Chào mn! Hôm nay mik chia sẻ hướng dẫn lập trình FastAPI backend cực hay với Docker tại https://devradar.io</p>\n```python\nfrom fastapi import FastAPI\napp = FastAPI()\n```"
    }

    response = client.post("/api/v1/quality/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["is_it"] is True
    assert "it_probability" in data
    assert "quality_score" in data
    assert "quality_level" in data
    assert data["statistics"]["word_count"] > 0
    assert data["statistics"]["code_blocks"] >= 1
    assert data["statistics"]["urls"] >= 1


def test_analyze_comment_endpoint():
    payload = {
        "content": "Cảm ơn bạn bài viết rất bổ ích, mình đã áp dụng thành công!",
        "content_type": "comment"
    }
    response = client.post("/api/v1/quality/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert data["toxicity"]["label"] == "safe"


def test_ai_status_endpoint():
    response = client.get("/api/v1/quality/ai-status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "api_key_configured" in data
    assert data["api_key_configured"] is True
