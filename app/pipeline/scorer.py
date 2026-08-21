from typing import Dict, Any, Tuple
from app.core.config import settings


class QualityScorer:
    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or settings.get_scoring_weights()

    def calculate_score(
        self,
        classification_result: Dict[str, Any],
        analyzer_result: Dict[str, Any],
        statistics: Dict[str, Any]
    ) -> Tuple[int, str]:
        """
        Tính điểm Quality Score (0-100) và xếp loại Quality Level.
        """
        # 1. Relevance Score (Dựa trên IT Probability)
        it_prob = classification_result.get("it_probability", 0.5)
        relevance_score = it_prob * 100.0

        # 2. Safety Score (Dựa trên Toxicity)
        toxicity = classification_result.get("toxicity", {})
        toxic_label = toxicity.get("label", "safe")
        toxic_prob = toxicity.get("probability", 0.0)

        if toxic_label == "toxic":
            safety_score = max(0.0, (1.0 - toxic_prob) * 100.0)
        elif toxic_label == "suspicious":
            safety_score = 60.0
        else:
            safety_score = 100.0

        # 3. Readability & Structure & ContentQuality (Dựa trên Rules & Metrics)
        total_penalty = analyzer_result.get("total_penalty", 0.0)

        # Lấy riêng các metrics
        word_count = statistics.get("word_count", 0)
        teencode_count = statistics.get("teencode_count", 0)
        typo_count = statistics.get("typo_count", 0)

        # Penalty cho teencode & typo trên tổng số từ
        typo_ratio = (teencode_count + typo_count) / max(word_count, 1)
        readability_score = max(0.0, (1.0 - (total_penalty * 0.5 + typo_ratio * 2.0)) * 100.0)

        structure_score = max(0.0, (1.0 - total_penalty) * 100.0)
        content_quality_score = max(0.0, (1.0 - (total_penalty * 0.7)) * 100.0)

        # 4. Tổng hợp với Trọng số
        w_rel = self.weights.get("relevance", 0.25)
        w_read = self.weights.get("readability", 0.20)
        w_struct = self.weights.get("structure", 0.20)
        w_safe = self.weights.get("safety", 0.20)
        w_qual = self.weights.get("content_quality", 0.15)

        raw_score = (
            w_rel * relevance_score +
            w_read * readability_score +
            w_struct * structure_score +
            w_safe * safety_score +
            w_qual * content_quality_score
        )

        final_score = int(round(max(0.0, min(100.0, raw_score))))

        # 5. Phân loại Quality Level
        if final_score >= 90:
            level = "excellent"
        elif final_score >= 75:
            level = "good"
        elif final_score >= 50:
            level = "average"
        else:
            level = "poor"

        return final_score, level
