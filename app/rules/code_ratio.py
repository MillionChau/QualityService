from typing import Dict, Any
from app.rules.base import BaseRule


class CodeRatioRule(BaseRule):
    name: str = "code_ratio_rule"

    def evaluate(self, text: str, statistics: Dict[str, Any], protected_map: Dict[str, Any]) -> Dict[str, Any]:
        code_blocks_count = statistics.get("code_blocks", 0)
        word_count = max(statistics.get("word_count", 1), 1)

        # Tính tổng chiều dài ký tự của tất cả các block/inline code trong protected_map
        code_char_len = sum(len(v) for k, v in protected_map.items() if k.startswith("[[CODE_") or k.startswith("[[INLINE_CODE_"))

        total_char_len = max(len(text) + code_char_len, 1)

        code_ratio = code_char_len / total_char_len

        issues = []
        score = 1.0
        penalty = 0.0

        if code_ratio > 0.85:
            penalty = 0.3
            score = 0.6
            issues.append({
                "type": "code_ratio",
                "original": f"Code Ratio: {round(code_ratio * 100, 1)}%",
                "corrected": None,
                "confidence": 0.9,
                "message": "Bài viết chứa quá nhiều mã nguồn thô và quá ít lời giải thích (> 85% code)."
            })

        return {
            "score": score,
            "penalty": penalty,
            "issues": issues,
            "metrics": {
                "code_ratio": round(code_ratio, 4),
                "code_blocks": code_blocks_count
            }
        }
