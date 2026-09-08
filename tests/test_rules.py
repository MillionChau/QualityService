from app.pipeline.quality_analyzer import QualityAnalyzerEngine


def test_quality_rules_evaluation():
    analyzer = QualityAnalyzerEngine()

    text_with_emoji = "Bài viết này có quá nhiều emoji 😀😁😂😃😄😅😆"
    stats = {
        "word_count": 8,
        "sentence_count": 1,
        "paragraph_count": 1,
        "code_blocks": 0,
        "urls": 0,
        "emoji_count": 7,
        "teencode_count": 0,
        "typo_count": 0
    }
    protected_map = {}

    res = analyzer.analyze(text_with_emoji, stats, protected_map)

    assert any(i["type"] == "emoji_excess" for i in res["issues"])
    assert not any(i["type"] == "length" for i in res["issues"])
    assert res["total_penalty"] > 0

