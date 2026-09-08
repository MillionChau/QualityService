import os
import re
import joblib
from typing import Tuple, Optional
from app.core.config import settings
from app.core.logging import logger


class ToxicClassifier:
    """
    Phân loại nội dung độc hại (Toxic Content) bằng Heuristic Profanity Guard
    kết hợp ML Model (.pkl / .bin).
    """

    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.loaded_pkl = False
        self.loaded_fasttext = False

        self.toxic_keywords = set()
        self.toxic_slang_patterns = []
        self.load_keywords()

    def load_keywords(self):
        """
        Nạp danh sách từ khóa & regex pattern thô tục linh hoạt từ file JSON dynamic.
        """
        from pathlib import Path
        import json
        json_path = Path(__file__).parent.parent / "dictionaries" / "toxic_keywords.json"
        if json_path.exists():
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.toxic_keywords = set(data.get("keywords", []))
                        self.toxic_slang_patterns = data.get("slang_patterns", [])
                        logger.info(f"Loaded {len(self.toxic_keywords)} toxic keywords and {len(self.toxic_slang_patterns)} slang patterns from {json_path.name}")
                        return
            except Exception as e:
                logger.error(f"Error loading dynamic toxic keywords: {e}")

        # Fallback từ khóa mặc định nếu chưa nạp được JSON
        self.toxic_keywords = {
            "độc hại", "lừa đảo", "scam", "chửi", "xúc phạm", "spam", "hack", "crack",
            "ngu", "đồ ngu", "ngu học", "óc chó", "súc vật", "chó đẻ", "mất dạy",
            "mẹ kiếp", "bố láo", "khùng", "điên", "hãm", "hãm lồn", "rác rưởi", "phốt",
            "tẩy chay", "bắt nạt", "văng tục", "chửi thề", "gian dối", "gian lận",
            "đồ khốn", "khốn nạn", "khốn kiếp", "khốn", "biến đi", "cút đi", "cút",
            "thằng", "bực mình", "bực cả mình", "ngu ngốc", "lừa tiền"
        }
        self.toxic_slang_patterns = [
            r"\bdm\b", r"\bdkm\b", r"\bvkl\b", r"\bvl\b", r"\bcl\b", r"\bcmm\b",
            r"\bcon cặc\b", r"\bcặc\b", r"\blồn\b", r"\bbuồi\b", r"\bđít\b", r"\bđái\b", r"\bỉa\b",
            r"\bđồ khốn\b", r"\bkhốn\b", r"\bbiến đi\b", r"\bmẹ kiếp\b", r"\bsúc vật\b", r"\bóc chó\b"
        ]

    @property
    def loaded(self) -> bool:
        return self.loaded_pkl or self.loaded_fasttext

    def load_model(self):
        # 1. Thử nạp mô hình PKL (TF-IDF + LogisticRegression)
        if os.path.exists(settings.TOXIC_PKL_MODEL_PATH) and os.path.exists(settings.TOXIC_PKL_VECTORIZER_PATH):
            try:
                self.model = joblib.load(settings.TOXIC_PKL_MODEL_PATH)
                self.vectorizer = joblib.load(settings.TOXIC_PKL_VECTORIZER_PATH)
                self.loaded_pkl = True
                logger.info(f"Loaded Toxic PKL model from {settings.TOXIC_PKL_MODEL_PATH}")
                return
            except Exception as e:
                logger.error(f"Failed to load Toxic PKL model: {e}")

        # 2. Thử nạp mô hình FastText (.bin)
        if os.path.exists(settings.TOXIC_MODEL_PATH):
            try:
                import fasttext
                self.model = fasttext.load_model(settings.TOXIC_MODEL_PATH)
                self.loaded_fasttext = True
                logger.info(f"Loaded FastText Toxic model from {settings.TOXIC_MODEL_PATH}")
                return
            except Exception as e:
                logger.error(f"Failed to load FastText Toxic model: {e}")

        logger.info("Toxic ML model files not found. Using Advanced Profanity Heuristic Classifier.")

    def check_heuristic_profanity(self, text: str) -> Tuple[Optional[str], float]:
        """
        Kiểm tra từ khóa / từ lóng thô tục chửi thề với độ ưu tiên tuyệt đối.
        """
        text_lower = text.lower()
        toxic_hits = sum(1 for kw in self.toxic_keywords if kw in text_lower)
        slang_hits = sum(1 for pat in self.toxic_slang_patterns if re.search(pat, text_lower))

        total_score = toxic_hits + (slang_hits * 2)

        if total_score >= 2 or slang_hits >= 1:
            return "toxic", 0.92
        elif total_score >= 1:
            return "suspicious", 0.65

        return None, 0.0

    def predict(self, text: str) -> Tuple[str, float]:
        """
        Dự đoán mức độ độc hại của bài viết.
        Trả về (label, probability).
        labels: 'safe', 'suspicious', 'toxic'
        """
        # 1. Chạy Heuristic Profanity Guard trước (Ưu tiên hàng đầu cho chửi thề, văng tục)
        heur_label, heur_prob = self.check_heuristic_profanity(text)
        if heur_label == "toxic":
            return "toxic", heur_prob

        # 2. Inference từ mô hình PKL (nếu có)
        if self.loaded_pkl and self.model and self.vectorizer:
            try:
                from app.pipeline.tokenizer import VietnameseTokenizer
                tokenizer = VietnameseTokenizer()
                tokenized_text = tokenizer.tokenize(text)
                X_vector = self.vectorizer.transform([tokenized_text])
                classes = list(self.model.classes_)
                probs = self.model.predict_proba(X_vector)[0]

                toxic_idx = classes.index("toxic") if "toxic" in classes else (1 if 1 in classes else -1)
                if toxic_idx != -1:
                    prob = float(probs[toxic_idx])
                    if prob >= 0.50:
                        return "toxic", round(prob, 4)
                    elif prob >= 0.35:
                        return "suspicious", round(prob, 4)
            except Exception as e:
                logger.error(f"Error during PKL Toxic inference: {e}")

        # 3. Inference từ FastText (nếu có)
        if self.loaded_fasttext and self.model:
            try:
                labels, probabilities = self.model.predict(text.replace("\n", " "))
                label_str = labels[0].replace("__label__", "").lower()
                prob = float(probabilities[0])

                if prob >= settings.TOXIC_HIGH_THRESHOLD:
                    return "toxic", round(prob, 4)
                elif prob >= settings.TOXIC_SUSPICIOUS_THRESHOLD:
                    return "suspicious", round(prob, 4)
            except Exception as e:
                logger.error(f"Error during FastText Toxic inference: {e}")

        if heur_label == "suspicious":
            return "suspicious", heur_prob

        return "safe", 0.95


