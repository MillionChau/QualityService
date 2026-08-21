from typing import Dict, Any
from app.rules.base import BaseRule


class LengthRule(BaseRule):
    name: str = "length_rule"

    def evaluate(self, text: str, statistics: Dict[str, Any], protected_map: Dict[str, Any]) -> Dict[str, Any]:
        word_count = statistics.get("word_count", 0)
        issues = []
        score = 1.0
        penalty = 0.0

        if word_count < 30:
            score = 0.3
            penalty = 0.4
            issues.append({
                "type": "length",
                "original": f"Word count: {word_count}",
                "corrected": None,
                "confidence": 1.0,
                "message": "Bài viết quá ngắn (< 30 từ), thiếu thông tin truyền tải."
            })
        elif word_count < 100:
            score = 0.7
            penalty = 0.15
            issues.append({
                "type": "length",
                "original": f"Word count: {word_count}",
                "corrected": None,
                "confidence": 0.9,
                "message": "Bài viết hơi ngắn (< 100 từ)."
            })
        elif word_count > 5000:
            score = 0.8
            penalty = 0.1
            issues.append({
                "type": "length",
                "original": f"Word count: {word_count}",
                "corrected": None,
                "confidence": 0.8,
                "message": "Bài viết quá dài (> 5000 từ), nên chia nhỏ thành các phần."
            })

        return {
            "score": score,
            "penalty": penalty,
            "issues": issues,
            "metrics": {"word_count": word_count}
        }
