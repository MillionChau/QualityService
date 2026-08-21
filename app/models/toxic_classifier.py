import os
from typing import Tuple, Dict, Any
from app.core.config import settings
from app.core.logging import logger


class ToxicClassifier:
    """
    Phân loại nội dung độc hại (Toxic Content) bằng FastText (.bin).
    Có sẵn fallback heuristic nếu chưa nạp được file model .bin.
    """

    def __init__(self):
        self.model = None
        self.loaded = False
        self.toxic_keywords = {
            "độc hại", "lừa đảo", "scam", "chửi", "xúc phạm", "spam", "hack", "crack"
        }

    def load_model(self):
        if os.path.exists(settings.TOXIC_MODEL_PATH):
            try:
                import fasttext
                self.model = fasttext.load_model(settings.TOXIC_MODEL_PATH)
                self.loaded = True
                logger.info(f"Loaded FastText Toxic model from {settings.TOXIC_MODEL_PATH}")
            except Exception as e:
                logger.error(f"Failed to load FastText Toxic model: {e}")
                self.loaded = False
        else:
            logger.info("FastText Toxic model file not found. Using Heuristic Toxic Fallback Classifier.")
            self.loaded = False

    def predict(self, text: str) -> Tuple[str, float]:
        """
        Dự đoán mức độ độc hại của bài viết.
        Trả về (label, probability).
        labels: 'safe', 'suspicious', 'toxic'
        """
        if self.loaded and self.model:
            try:
                # FastText predict trả về labels và proba
                labels, probabilities = self.model.predict(text.replace("\n", " "))
                label_str = labels[0].replace("__label__", "").lower()
                prob = float(probabilities[0])

                if prob >= settings.TOXIC_HIGH_THRESHOLD:
                    return "toxic", round(prob, 4)
                elif prob >= settings.TOXIC_SUSPICIOUS_THRESHOLD:
                    return "suspicious", round(prob, 4)
                else:
                    return "safe", round(1.0 - prob if label_str != "safe" else prob, 4)
            except Exception as e:
                logger.error(f"Error during FastText inference: {e}")

        # Fallback Heuristic
        text_lower = text.lower()
        toxic_hits = sum(1 for kw in self.toxic_keywords if kw in text_lower)
        if toxic_hits >= 3:
            return "toxic", 0.85
        elif toxic_hits >= 1:
            return "suspicious", 0.55

        return "safe", 0.95
