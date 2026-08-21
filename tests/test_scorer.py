from app.pipeline.scorer import QualityScorer


def test_quality_scorer_calculation():
    scorer = QualityScorer()

    classification_res = {
        "is_it": True,
        "it_probability": 0.95,
        "toxicity": {"label": "safe", "probability": 0.98}
    }
    analyzer_res = {
        "total_penalty": 0.05,
        "issues": []
    }
    stats = {
        "word_count": 300,
        "teencode_count": 0,
        "typo_count": 0
    }

    score, level = scorer.calculate_score(classification_res, analyzer_res, stats)

    assert 80 <= score <= 100
    assert level in ["excellent", "good"]
