from app.pipeline.quality_analyzer import QualityAnalyzerEngine


def test_quality_rules_evaluation():
    analyzer = QualityAnalyzerEngine()

    short_text = "Bài ngắn nè."
    stats = {
        "word_count": 3,
        "sentence_count": 1,
        "paragraph_count": 1,
        "code_blocks": 0,
        "urls": 0,
        "emoji_count": 0,
        "teencode_count": 0,
        "typo_count": 0
    }
    protected_map = {}

    res = analyzer.analyze(short_text, stats, protected_map)

    assert len(res["issues"]) > 0
    assert any(i["type"] == "length" for i in res["issues"])
    assert res["total_penalty"] > 0
