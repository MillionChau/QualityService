import os
import joblib
import re
from typing import Tuple
from app.core.config import settings
from app.core.logging import logger


class ITDomainClassifier:
    """
    Phân loại bài viết thuộc lĩnh vực CNTT (IT Domain) bằng TF-IDF + Logistic Regression.
    Có sẵn fallback heuristic nếu chưa nạp được file model .pkl.
    """

    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.loaded = False
        self.it_keywords = set()
        self.load_keywords()

    def load_keywords(self):
        """
        Nạp danh sách từ khóa IT linh hoạt từ file JSON cấu hình dynamic.
        """
        from pathlib import Path
        import json
        json_path = Path(__file__).parent.parent / "dictionaries" / "it_keywords.json"
        if json_path.exists():
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.it_keywords = set(data)
                        logger.info(f"Loaded {len(self.it_keywords)} dynamic IT keywords from {json_path.name}")
                        return
            except Exception as e:
                logger.error(f"Error loading dynamic IT keywords: {e}")

        # Fallback từ khóa mặc định nếu chưa nạp được JSON
        self.it_keywords = {
            "python", "javascript", "react", "vue", "angular", "dotnet", "c#", "java", "golang",
            "docker", "kubernetes", "api", "fastapi", "backend", "frontend", "database", "sql",
            "nosql", "redis", "mongodb", "git", "ci/cd", "devops", "cloud", "aws", "azure",
            "algorithm", "code", "coder", "lap trinh", "lập trình", "phần mềm", "thuật toán",
            "framework", "microservice", "fullstack", "server", "linux", "ai", "ml", "machine learning"
        }

    def load_model(self):
        if os.path.exists(settings.IT_MODEL_PATH) and os.path.exists(settings.IT_VECTORIZER_PATH):
            try:
                self.model = joblib.load(settings.IT_MODEL_PATH)
                self.vectorizer = joblib.load(settings.IT_VECTORIZER_PATH)
                self.loaded = True
                logger.info(f"Loaded IT Classifier model from {settings.IT_MODEL_PATH}")
            except Exception as e:
                logger.error(f"Failed to load IT Classifier model: {e}")
                self.loaded = False
        else:
            logger.info("IT Classifier model files not found. Using Heuristic Keyword Fallback Classifier.")
            self.loaded = False

    def count_it_keywords(self, text: str) -> int:
        text_lower = text.lower()
        hits = 0
        for kw in self.it_keywords:
            # Ngăn chặn khớp nhầm từ ngắn (VD: 'ai' khớp trong 'hai', 'ml' trong 'làm', 'c#'...)
            if len(kw) <= 3:
                pattern = r"\b" + re.escape(kw) + r"\b"
                if re.search(pattern, text_lower):
                    hits += 1
            else:
                if kw in text_lower:
                    hits += 1
        return hits

    def predict(self, text: str) -> Tuple[bool, float]:
        """
        Dự đoán bài viết có thuộc IT domain hay không.
        Trả về (is_it, probability).
        """
        keyword_hits = self.count_it_keywords(text)

        if self.loaded and self.model and self.vectorizer:
            try:
                from app.pipeline.tokenizer import VietnameseTokenizer
                tokenizer = VietnameseTokenizer()
                tokenized_text = tokenizer.tokenize(text)
                X_vector = self.vectorizer.transform([tokenized_text])
                prob = float(self.model.predict_proba(X_vector)[0][1])

                # Kết hợp xác suất ML và Keyword Hits linh hoạt:
                if keyword_hits >= 2:
                    prob = max(prob, 0.85)
                elif keyword_hits >= 1:
                    prob = max(prob, 0.65)
                elif prob < 0.40 and keyword_hits == 0:
                    # Chỉ giảm xác suất nếu ML rất không chắc chắn (< 0.40) và hoàn toàn không có từ khóa
                    prob = min(prob, 0.25)

                is_it = prob >= settings.IT_THRESHOLD
                return is_it, round(prob, 4)
            except Exception as e:
                logger.error(f"Error during ML IT classification inference: {e}")

        # Fallback Heuristic
        text_lower = text.lower()
        word_count = max(len(text_lower.split()), 1)
        density = keyword_hits / min(word_count, 100)

        # Tính xác suất sơ bộ dựa trên mật độ từ khóa IT
        if keyword_hits == 0:
            prob = 0.15
        elif keyword_hits == 1:
            prob = 0.45
        else:
            prob = min(0.60 + (keyword_hits * 0.10) + (density * 1.5), 0.98)

        is_it = prob >= settings.IT_THRESHOLD
        return is_it, round(prob, 4)
