import re
from typing import Tuple, Dict, List
import emoji


class TextCleaner:
    def __init__(self):
        # Regex patterns for content protection
        self.code_block_pattern = re.compile(r"```[\s\S]*?```", re.MULTILINE)
        self.inline_code_pattern = re.compile(r"`[^`\n]+`")
        self.url_pattern = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
        self.html_tag_pattern = re.compile(r"<[^>]+>")



    def clean(self, raw_text: str) -> Tuple[str, Dict[str, str], Dict[str, int]]:
        """
        Bảo vệ code/URL -> Làm sạch HTML/whitespace -> Demojize Emoji.
        Trả về (cleaned_text, protected_map, counts)
        """
        protected_map: Dict[str, str] = {}
        counts = {
            "code_blocks": 0,
            "urls": 0,
            "emoji_count": 0
        }

        current_text = raw_text or ""

        # 1. Bảo vệ Code Blocks
        def replace_code_block(match):
            nonlocal counts
            placeholder = f"[[CODE_BLOCK_{len(protected_map)}]]"
            protected_map[placeholder] = match.group(0)
            counts["code_blocks"] += 1
            return placeholder

        current_text = self.code_block_pattern.sub(replace_code_block, current_text)

        # 2. Bảo vệ Inline Code
        def replace_inline_code(match):
            nonlocal counts
            placeholder = f"[[INLINE_CODE_{len(protected_map)}]]"
            protected_map[placeholder] = match.group(0)
            counts["code_blocks"] += 1
            return placeholder

        current_text = self.inline_code_pattern.sub(replace_inline_code, current_text)

        # 3. Bảo vệ URL
        def replace_url(match):
            nonlocal counts
            placeholder = f"[[URL_{len(protected_map)}]]"
            protected_map[placeholder] = match.group(0)
            counts["urls"] += 1
            return placeholder

        current_text = self.url_pattern.sub(replace_url, current_text)

        # 4. Làm sạch HTML tags
        current_text = self.html_tag_pattern.sub(" ", current_text)


        # 5. Loại bỏ Control characters ngoại trừ newline
        current_text = "".join(ch for ch in current_text if ch == "\n" or ch == "\t" or (ord(ch) >= 32 and ord(ch) != 127))

        # 6. Emoji Handling & Counting
        emoji_count = emoji.emoji_count(current_text)
        counts["emoji_count"] = emoji_count
        if emoji_count > 0:
            current_text = emoji.demojize(current_text, language="vi")

        # 7. Chuẩn hóa whitespace thừa (giữ lại cấu trúc đoạn văn \n\n)
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in current_text.split("\n")]
        cleaned_text = "\n".join(lines).strip()

        return cleaned_text, protected_map, counts

    @staticmethod
    def restore(text: str, protected_map: Dict[str, str]) -> str:
        """Khoan phục lại các nội dung protected theo thứ tự."""
        restored = text
        for placeholder, original in protected_map.items():
            restored = restored.replace(placeholder, original)
        return restored
