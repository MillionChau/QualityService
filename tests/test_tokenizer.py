from app.pipeline.tokenizer import VietnameseTokenizer


def test_tokenizer_protected_placeholders():
    tokenizer = VietnameseTokenizer()
    text = "Trí tuệ nhân tạo phát triển mạnh cùng [[CODE_BLOCK_0]] và [[URL_0]]"

    segmented = tokenizer.tokenize(text)

    # Placeholder phải được giữ nguyên vẹn
    assert "[[CODE_BLOCK_0]]" in segmented
    assert "[[URL_0]]" in segmented

    assert "Trí_tuệ" in segmented or "nhân_tạo" in segmented or "Trí tuệ" in segmented
