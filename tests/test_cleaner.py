from app.pipeline.cleaner import TextCleaner


def test_text_cleaner_protection_and_html():
    cleaner = TextCleaner()
    raw_text = "<p>Chào mn! Đây là câu lệnh `print('hello')` và link https://devradar.io</p>\n```python\ndef test():\n    pass\n```"

    cleaned_text, protected_map, counts = cleaner.clean(raw_text)

    # Kiểm tra số lượng protected items
    assert counts["code_blocks"] == 2  # 1 block code, 1 inline code
    assert counts["urls"] == 1

    # Kiểm tra placeholder tồn tại trong cleaned_text
    assert "[[INLINE_CODE_" in cleaned_text or "[[CODE_BLOCK_" in cleaned_text
    assert "[[URL_" in cleaned_text
    assert "<p>" not in cleaned_text


    # Kiểm tra khôi phục lại (restore)
    restored = cleaner.restore(cleaned_text, protected_map)
    assert "print('hello')" in restored
    assert "https://devradar.io" in restored
    assert "def test():" in restored
