import re
from typing import Dict
from app.core.logging import logger

try:
    from underthesea import word_tokenize
except Exception as e:
    logger.warning(f"Underthesea library not available ({e}). Using Regex word tokenizer fallback.")
    word_tokenize = None


class VietnameseTokenizer:
    def __init__(self):
        self.placeholder_pattern = re.compile(r"\[\[(CODE_BLOCK|INLINE_CODE|URL)_\d+\]\]")


    def tokenize(self, text: str) -> str:
        """
        Thực hiện Word Segmentation bằng Underthesea (hoặc Fallback).
        Bảo vệ các thẻ placeholder <CODE_BLOCK_...>, <URL_...> không bị tách từ nhầm.
        """
        if not text:
            return ""

        # Tách text theo ranh giới placeholders
        parts = []
        last_idx = 0

        for match in self.placeholder_pattern.finditer(text):
            start, end = match.span()
            if start > last_idx:
                segment = text[last_idx:start]
                tokenized_segment = self._tokenize_segment(segment)
                parts.append(tokenized_segment)

            # Thêm placeholder nguyên vẹn
            parts.append(match.group(0))
            last_idx = end

        if last_idx < len(text):
            segment = text[last_idx:]
            tokenized_segment = self._tokenize_segment(segment)
            parts.append(tokenized_segment)

        return " ".join(parts)

    def _tokenize_segment(self, segment: str) -> str:
        if word_tokenize is not None:
            try:
                return word_tokenize(segment, format="text")
            except Exception as e:
                logger.warning(f"Underthesea tokenize error on segment: {e}")

        return segment

