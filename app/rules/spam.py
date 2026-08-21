import re
from typing import Dict, Any
from app.rules.base import BaseRule


class SpamRule(BaseRule):
    name: str = "spam_rule"

    def __init__(self):
        # Phát hiện ký tự lặp liên tiếp 4 lần trở lên (ví dụ: "aaaaa", "!!!!!")
        self.repeated_chars_pattern = re.compile(r"(.)\1{4,}")

    def evaluate(self, text: str, statistics: Dict[str, Any], protected_map: Dict[str, Any]) -> Dict[str, Any]:
        issues = []
        matches = self.repeated_chars_pattern.findall(text)
        penalty = 0.0
        score = 1.0

        if len(matches) > 0:
            penalty = min(len(matches) * 0.15, 0.6)
            score = max(1.0 - penalty, 0.2)
            issues.append({
                "type": "spam",
                "original": f"Repeated chars count: {len(matches)}",
                "corrected": None,
                "confidence": 1.0,
                "message": f"Phát hiện {len(matches)} vị trí chứa ký tự/dấu lặp đi lặp lại bất thường."
            })

        return {
            "score": score,
            "penalty": penalty,
            "issues": issues,
            "metrics": {"repeated_char_instances": len(matches)}
        }
