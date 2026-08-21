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

    def predict(self, text: str) -> Tuple[bool, float]:
        """
        Dự đoán bài viết có thuộc IT domain hay không.
        Trả về (is_it, probability).
        """
        if self.loaded and self.model and self.vectorizer:
            try:
                X_vector = self.vectorizer.transform([text])
                prob = float(self.model.predict_proba(X_vector)[0][1])
                is_it = prob >= settings.IT_THRESHOLD
                return is_it, prob
            except Exception as e:
                logger.error(f"Error during ML IT classification inference: {e}")

        # Fallback Heuristic
        text_lower = text.lower()
        keyword_hits = sum(1 for kw in self.it_keywords if kw in text_lower)
        word_count = max(len(text_lower.split()), 1)
        density = keyword_hits / min(word_count, 100)

        # Tính xác suất sơ bộ dựa trên mật độ từ khóa IT
        prob = min(0.35 + (keyword_hits * 0.15) + (density * 2.0), 0.98)
        if keyword_hits == 0:
            prob = 0.20

        is_it = prob >= settings.IT_THRESHOLD
        return is_it, round(prob, 4)
