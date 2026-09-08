# 🧪 DevRadar API Testing Guide: Crawler & Quality Services

Tài liệu thiết kế kịch bản test API cho 2 microservices:
- **CrawlerGithubService** (Port: `8000`)
- **QualityService** (Port: `8001`)

---

## 📑 Mục lục
1. [CrawlerGithubService APIs (`http://localhost:8000`)](#1-crawlergithubservice-apis-httplocalhost8000)
   - [1.1 Health & Service Info](#11-health--service-info)
   - [1.2 Scheduler & Manual Crawl](#12-scheduler--manual-crawl)
   - [1.3 Repository & Language Health Models](#13-repository--language-health-models)
   - [1.4 Trend Analysis & Model Retraining](#14-trend-analysis--model-retraining)
   - [1.5 Crawl Configuration & Analytics Logs](#15-crawl-configuration--analytics-logs)
2. [QualityService APIs (`http://localhost:8001`)](#2-qualityservice-apis-httplocalhost8001)
   - [2.1 Health & Component Status](#21-health--component-status)
   - [2.2 Article Quality Analysis](#22-article-quality-analysis)
3. [Kịch bản Kiểm thử Ranh giới (Edge Cases & Error Handling)](#3-kịch-bản-kiểm-thử-ranh-giới-edge-cases--error-handling)

---

# 1. CrawlerGithubService APIs (`http://localhost:8000`)

### 1.1 Health & Service Info

#### `GET /` - Service Overview
* **Mục đích**: Kiểm tra service root và đường dẫn tài liệu.
* **cURL Command**:
  ```bash
  curl -X GET "http://localhost:8000/"
  ```
* **Expected Response (200 OK)**:
  ```json
  {
    "service": "CrawlerGithubService",
    "database": "MongoDB Atlas",
    "status": "running",
    "docs": "/docs",
    "scheduler": "/scheduler/status"
  }
  ```

#### `GET /health` - Health Check
* **Mục đích**: Kiểm tra kết nối MongoDB Atlas.
* **cURL Command**:
  ```bash
  curl -X GET "http://localhost:8000/health"
  ```
* **Expected Response (200 OK)**:
  ```json
  {
    "status": "healthy",
    "service": "CrawlerGithubService",
    "mongodb_connected": true
  }
  ```

---

### 1.2 Scheduler & Manual Crawl

#### `GET /scheduler/status` - Scheduler Status
* **Mục đích**: Kiểm tra trạng thái APScheduler và danh sách các job định kỳ.
* **cURL Command**:
  ```bash
  curl -X GET "http://localhost:8000/scheduler/status"
  ```
* **Expected Response (200 OK)**:
  ```json
  {
    "scheduler_running": true,
    "jobs": [
      {
        "id": "scheduled_crawl_job",
        "name": "scheduled_crawl_job",
        "next_run_time": "2026-08-28 12:00:00+07:00"
      }
    ]
  }
  ```

#### `POST /scheduler/trigger-now` - Trigger Background Crawl Job
* **Mục đích**: Kích hoạt job cào dữ liệu chạy ngầm ngay lập tức.
* **cURL Command**:
  ```bash
  curl -X POST "http://localhost:8000/scheduler/trigger-now"
  ```
* **Expected Response (200 OK)**:
  ```json
  {
    "status": "success",
    "message": "Scheduled crawl job triggered in background."
  }
  ```

#### `POST /crawl` - Manual Sync Crawl
* **Mục đích**: Chạy cào trực tiếp đồng bộ với từ khóa tìm kiếm tùy chỉnh.
* **Query Parameters**:
  - `query` *(string, optional)*: Từ khóa tìm kiếm GitHub (Mặc định: `stars:>10000`)
  - `max_repos` *(int, optional)*: Số lượng repos tối đa (Mặc định: `5`)
* **cURL Command**:
  ```bash
  curl -X POST "http://localhost:8000/crawl?query=language:python+stars:>5000&max_repos=2"
  ```
* **Expected Response (200 OK)**:
  ```json
  {
    "status": "success",
    "processed_count": 2,
    "data": [
      {
        "full_name": "tiangolo/fastapi",
        "stars": 75000,
        "language": "Python"
      }
    ]
  }
  ```

---

### 1.3 Repository & Language Health Models

#### `POST /analytics/repository-health` - Evaluate Repository Health
* **Mục đích**: Tính toán điểm sức khỏe Repository (0 - 100) & xếp loại (`HEALTHY`, `MODERATE`, `AT_RISK`, `CRITICAL`).
* **Headers**: `Content-Type: application/json`
* **cURL Command**:
  ```bash
  curl -X POST "http://localhost:8000/analytics/repository-health" \
    -H "Content-Type: application/json" \
    -d '{
      "full_name": "facebook/react",
      "stars": 220000,
      "forks": 45000,
      "open_issues": 800,
      "closed_issues_30d": 120,
      "contributors_count": 1500,
      "recent_commits_30d": 85,
      "days_since_last_push": 1,
      "star_growth_rate_30d": 0.04
    }'
  ```
* **Expected Response (200 OK)**:
  ```json
  {
    "full_name": "facebook/react",
    "health_score": 92.5,
    "health_status": "HEALTHY",
    "components": {
      "activity_score": 95.0,
      "community_score": 90.0,
      "maintenance_score": 92.5
    }
  }
  ```

#### `POST /analytics/language-health` - Evaluate Language Health
* **Mục đích**: Đánh giá chỉ số sức khỏe & sự phát triển của một Ngôn ngữ lập trình.
* **cURL Command**:
  ```bash
  curl -X POST "http://localhost:8000/analytics/language-health" \
    -H "Content-Type: application/json" \
    -d '{
      "language": "Python",
      "repository_count": 15000,
      "total_stars": 850000,
      "total_forks": 210000,
      "commit_activity_index": 88.5,
      "contributor_activity_index": 91.0,
      "repo_growth_rate": 0.08,
      "star_growth_rate": 0.12
    }'
  ```
* **Expected Response (200 OK)**:
  ```json
  {
    "language": "Python",
    "health_score": 89.2,
    "health_status": "HEALTHY"
  }
  ```

---

### 1.4 Trend Analysis & Model Retraining

#### `POST /analytics/trend-analysis` - Analyze Technology Trend
* **Mục đích**: Nhận diện giai đoạn xu hướng (`EMERGING`, `GROWING`, `STABLE`, `DECLINING`).
* **cURL Command**:
  ```bash
  curl -X POST "http://localhost:8000/analytics/trend-analysis" \
    -H "Content-Type: application/json" \
    -d '{
      "technology": "Rust",
      "series_values": [120, 145, 180, 230, 310, 420, 580]
    }'
  ```
* **Expected Response (200 OK)**:
  ```json
  {
    "technology": "Rust",
    "trend_status": "GROWING",
    "growth_rate": 0.29,
    "slope": 76.4
  }
  ```

#### `POST /analytics/retrain-now` - Trigger ML Retraining Job
* **Mục đích**: Kích hoạt cào lại dữ liệu và nạp lại mô hình huấn luyện ML.
* **cURL Command**:
  ```bash
  curl -X POST "http://localhost:8000/analytics/retrain-now"
  ```
* **Expected Response (200 OK)**:
  ```json
  {
    "status": "success",
    "message": "Daily Model Retraining & Data Sync job triggered in background."
  }
  ```

---

### 1.5 Crawl Configuration & Analytics Logs

#### `GET /analytics/crawl-config` - View Crawl Config
* **cURL Command**:
  ```bash
  curl -X GET "http://localhost:8000/analytics/crawl-config"
  ```

#### `POST /analytics/crawl-config` - Update Crawl Config
* **cURL Command**:
  ```bash
  curl -X POST "http://localhost:8000/analytics/crawl-config" \
    -H "Content-Type: application/json" \
    -d '{
      "crawl_interval_minutes": 120,
      "max_repos_per_job": 10
    }'
  ```

#### `GET /analytics/repository-health/history` - Get Repo Health History
* **cURL Command**:
  ```bash
  curl -X GET "http://localhost:8000/analytics/repository-health/history?full_name=facebook/react&limit=10"
  ```

---

# 2. QualityService APIs (`http://localhost:8001`)

### 2.1 Health & Component Status

#### `GET /` - Root Status
* **cURL Command**:
  ```bash
  curl -X GET "http://localhost:8001/"
  ```

#### `GET /api/v1/quality/health` - System & Component Health Check
* **Mục đích**: Đánh giá kết nối Elasticsearch, trạng thái Aho-Corasick automaton và các mô hình ML Classifiers.
* **cURL Command**:
  ```bash
  curl -X GET "http://localhost:8001/api/v1/quality/health"
  ```
* **Expected Response (200 OK)**:
  ```json
  {
    "status": "healthy",
    "service": "QualityService",
    "env": "development",
    "components": {
      "elasticsearch": { "status": "disabled", "reachable": false },
      "it_classifier_loaded": false,
      "toxic_classifier_loaded": false,
      "dictionary_automaton": true
    }
  }
  ```

#### `GET /api/v1/quality/models` - ML Models Status
* **cURL Command**:
  ```bash
  curl -X GET "http://localhost:8001/api/v1/quality/models"
  ```

#### `GET /api/v1/quality/dictionary/status` - Dictionary Automaton Status
* **cURL Command**:
  ```bash
  curl -X GET "http://localhost:8001/api/v1/quality/dictionary/status"
  ```

---

### 2.2 Article Quality Analysis

#### `POST /api/v1/quality/analyze` - Phân tích & Chấm điểm chất lượng bài viết

* **Mục đích**: Nhận nội dung bài viết kỹ thuật, tiến hành làm sạch, chuẩn hóa teencode/typo, phân loại IT domain & độc hại, đánh giá bằng Rule Engine và trả về điểm Quality Score.
* **Headers**: `Content-Type: application/json`

##### Request Sample 1: Bài viết chất lượng tốt (Python + FastAPI)
* **cURL Command**:
  ```bash
  curl -X POST "http://localhost:8001/api/v1/quality/analyze" \
    -H "Content-Type: application/json" \
    -d '{
      "content": "<h1>Hướng dẫn lập trình FastAPI Backend</h1><p>Chào mn! Hôm nay mik chia sẻ bài viết về cách tối ưu hóa hiệu năng ứng dụng `FastAPI` kết hợp với Docker và MongoDB tại https://devradar.io</p>\n```python\nfrom fastapi import FastAPI\napp = FastAPI()\n\n@app.get(\"/\")\ndef index():\n    return {\"status\": \"ok\"}\n```"
    }'
  ```

* **Expected Response (200 OK)**:
  ```json
  {
    "is_it": true,
    "it_probability": 0.95,
    "toxicity": {
      "label": "safe",
      "probability": 0.95
    },
    "quality_score": 88,
    "quality_level": "good",
    "statistics": {
      "word_count": 35,
      "sentence_count": 2,
      "paragraph_count": 1,
      "code_blocks": 1,
      "urls": 1,
      "emoji_count": 0,
      "teencode_count": 2,
      "typo_count": 0
    },
    "issues": [
      {
        "type": "teencode",
        "original": "mn",
        "corrected": "mọi người",
        "confidence": 1.0,
        "message": "Auto-replaced by Aho-Corasick (teencode)"
      },
      {
        "type": "teencode",
        "original": "mik",
        "corrected": "mình",
        "confidence": 1.0,
        "message": "Auto-replaced by Aho-Corasick (teencode)"
      }
    ],
    "cleaned_text": "Hướng dẫn lập trình FastAPI Backend Chào mọi người! Hôm nay mình chia sẻ bài viết về cách tối ưu hóa hiệu năng ứng dụng `FastAPI` kết hợp với Docker và MongoDB tại https://devradar.io\n```python\nfrom fastapi import FastAPI\napp = FastAPI()\n\n@app.get(\"/\")\ndef index():\n    return {\"status\": \"ok\"}\n```"
  }
  ```

##### Request Sample 2: Bài viết vi phạm (Spam & Ngắn)
* **cURL Command**:
  ```bash
  curl -X POST "http://localhost:8001/api/v1/quality/analyze" \
    -H "Content-Type: application/json" \
    -d '{
      "content": "KO CÓ GÌ ĐỂ XEM HẠHAHAHAHA 😃😃😃😃😃😃😃😃😃😃😃😃😃😃😃😃😃😃😃😃"
    }'
  ```

* **Expected Response (200 OK)**:
  ```json
  {
    "is_it": false,
    "it_probability": 0.20,
    "toxicity": {
      "label": "safe",
      "probability": 0.95
    },
    "quality_score": 32,
    "quality_level": "poor",
    "statistics": {
      "word_count": 7,
      "sentence_count": 1,
      "paragraph_count": 1,
      "code_blocks": 0,
      "urls": 0,
      "emoji_count": 20,
      "teencode_count": 1,
      "typo_count": 0
    },
    "issues": [
      {
        "type": "length",
        "original": "Word count: 7",
        "corrected": null,
        "confidence": 1.0,
        "message": "Bài viết quá ngắn (< 30 từ), thiếu thông tin truyền tải."
      },
      {
        "type": "emoji",
        "original": "Emoji count: 20",
        "corrected": null,
        "confidence": 0.9,
        "message": "Sử dụng quá nhiều Emoji làm giảm tính chuyên nghiệp của bài viết."
      }
    ]
  }
  ```

---

# 3. Kịch bản Kiểm thử Ranh giới (Edge Cases & Error Handling)

| Case STT | Endpoint | Payload / Điều kiện | Mã Lỗi Kỳ Vọng | Mô tả chi tiết |
| :--- | :--- | :--- | :--- | :--- |
| **TC-01** | `POST /api/v1/quality/analyze` | `{ "content": "" }` | `400 Bad Request` | Nội dung bài viết rỗng hoặc chỉ chứa khoảng trắng. |
| **TC-02** | `POST /api/v1/quality/analyze` | Không gửi trường `content` | `422 Unprocessable Entity` | Thiếu trường bắt buộc trong Pydantic schema validation. |
| **TC-03** | `POST /analytics/repository-health` | Sai kiểu dữ liệu (`stars: "invalid"`) | `422 Unprocessable Entity` | FastAPI/Pydantic báo lỗi định dạng kiểu dữ liệu. |
| **TC-04** | `GET /analytics/repository-health/history` | Gửi thiếu Query Param `full_name` | `422 Unprocessable Entity` | Tham số bắt buộc trên URL query string. |
