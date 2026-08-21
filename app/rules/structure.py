from typing import Dict, Any
from app.rules.base import BaseRule


class StructureRule(BaseRule):
    name: str = "structure_rule"

    def evaluate(self, text: str, statistics: Dict[str, Any], protected_map: Dict[str, Any]) -> Dict[str, Any]:
        sentence_count = statistics.get("sentence_count", 0)
        paragraph_count = statistics.get("paragraph_count", 0)
        word_count = statistics.get("word_count", 0)

        issues = []
        score = 1.0
        penalty = 0.0

        if word_count > 150 and paragraph_count <= 1:
            score = 0.6
            penalty = 0.2
            issues.append({
                "type": "structure",
                "original": f"Paragraphs: {paragraph_count}",
                "corrected": None,
                "confidence": 0.9,
                "message": "Bài viết dài nhưng không chia đoạn văn rõ ràng (chỉ có 1 khối văn bản)."
            })

        avg_words_per_sentence = word_count / max(sentence_count, 1)
        if avg_words_per_sentence > 60:
            score = min(score, 0.7)
            penalty += 0.15
            issues.append({
                "type": "structure",
                "original": f"Avg words/sentence: {round(avg_words_per_sentence, 1)}",
                "corrected": None,
                "confidence": 0.85,
                "message": "Các câu văn quá dài (> 60 từ/câu), khó đọc và phân tích."
            })

        return {
            "score": score,
            "penalty": penalty,
            "issues": issues,
            "metrics": {
                "avg_words_per_sentence": round(avg_words_per_sentence, 1),
                "paragraph_count": paragraph_count
            }
        }
