from typing import List, Dict, Any
from app.rules.base import BaseRule
from app.rules.spam import SpamRule
from app.rules.emoji import EmojiRule
from app.rules.structure import StructureRule
from app.rules.code_ratio import CodeRatioRule


class QualityAnalyzerEngine:
    def __init__(self, rules: List[BaseRule] = None):
        if rules is None:
            self.rules = [
                SpamRule(),
                EmojiRule(),
                StructureRule(),
                CodeRatioRule()
            ]
        else:
            self.rules = rules

    def analyze(self, text: str, statistics: Dict[str, Any], protected_map: Dict[str, Any]) -> Dict[str, Any]:
        rule_results = []
        all_issues = []
        total_penalty = 0.0

        for rule in self.rules:
            if getattr(rule, "enabled", True):
                res = rule.evaluate(text, statistics, protected_map)
                rule_results.append({
                    "rule_name": rule.name,
                    "score": res.get("score", 1.0),
                    "penalty": res.get("penalty", 0.0),
                    "metrics": res.get("metrics", {})
                })
                all_issues.extend(res.get("issues", []))
                total_penalty += res.get("penalty", 0.0)

        return {
            "rule_results": rule_results,
            "issues": all_issues,
            "total_penalty": min(total_penalty, 0.8)  # Tránh penalty vượt quá 80%
        }
