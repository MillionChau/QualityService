from typing import Dict, Any
from app.rules.base import BaseRule


class EmojiRule(BaseRule):
    name: str = "emoji_rule"

    def evaluate(self, text: str, statistics: Dict[str, Any], protected_map: Dict[str, Any]) -> Dict[str, Any]:
        emoji_count = statistics.get("emoji_count", 0)
        word_count = max(statistics.get("word_count", 1), 1)
        emoji_ratio = emoji_count / word_count

        issues = []
        score = 1.0
        penalty = 0.0

        if emoji_ratio > 0.15:  # > 15% số từ là emoji
            penalty = 0.3
            score = 0.5
            issues.append({
                "type": "emoji_excess",
                "original": f"Emoji count: {emoji_count}",
                "corrected": None,
                "confidence": 0.95,
                "message": f"Mật độ Emoji quá cao ({emoji_count} emoji / {word_count} từ)."
            })

        return {
            "score": score,
            "penalty": penalty,
            "issues": issues,
            "metrics": {"emoji_ratio": round(emoji_ratio, 4)}
        }
