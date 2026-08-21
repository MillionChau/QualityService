# DevRadar - Quality Service

Microservice trong hệ sinh thái **DevRadar**, chịu trách nhiệm tự động tiền xử lý, làm sạch, bảo vệ mã nguồn, chuẩn hóa từ ngữ tiếng Việt/teencode/typo, phân loại lĩnh vực CNTT & độc hại, đánh giá theo quy tắc (Rule Engine) và tính điểm chất lượng (Quality Score) bài viết.

---

## 🛠️ Công nghệ sử dụng
- **Python 3.11** + **FastAPI**
- **Regex**: Làm sạch HTML, tách URL/Code Block/Inline Code
- **emoji**: Demojize Emoji sang văn bản tiếng Việt
- **pyahocorasick**: Tra cứu từ điển teencode/typo/viết tắt tốc độ cao
- **underthesea**: Word segmentation tiếng Việt
- **scikit-learn**: TF-IDF + Logistic Regression (IT Domain Classifier)
- **FastText**: Toxic Classifier
- **Elasticsearch**: Fuzzy search tìm từ sai chính tả fallback

---

## 🚀 Hướng dẫn cài đặt & Chạy Local

### 1. Cài đặt Virtual Environment & Dependencies
```bash
cd services/Quality

# Tạo virtualenv
python -m venv venv

# Kích hoạt venv (Windows)
.\venv\Scripts\activate

# Cài đặt thư viện
pip install -r requirements.txt
```

### 2. Cấu hình môi trường `.env`
```bash
cp .env.example .env
```

### 3. Chạy Server Development
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```
- Swagger UI Documentation: `http://localhost:8001/docs`
- Health Check: `http://localhost:8001/api/v1/quality/health`

---

## 🧪 Chạy Kiểm thử (Tests)
```bash
pytest -v
```

---

## 🐳 Triển khai với Docker

```bash
# Build image
docker build -t devradar-quality-service .

# Run container
docker run -d -p 8001:8001 --name quality-service devradar-quality-service
```

---

## 📡 API Endpoints

### 1. `POST /api/v1/quality/analyze`
**Request Body:**
```json
{
  "content": "<h1>Học Python FastAPI</h1><p>Chào mn! Hôm nay mik chia sẻ bài viết về `fastapi` tại https://devradar.io</p>"
}
```

**Response Sample:**
```json
{
  "is_it": true,
  "it_probability": 0.95,
  "toxicity": {
    "label": "safe",
    "probability": 0.98
  },
  "quality_score": 88,
  "quality_level": "good",
  "statistics": {
    "word_count": 25,
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
    }
  ],
  "cleaned_text": "Học Python FastAPI Chào mọi người! Hôm nay mình chia sẻ bài viết về `fastapi` tại https://devradar.io"
}
```
