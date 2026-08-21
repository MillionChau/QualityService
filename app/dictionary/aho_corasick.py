from typing import Dict, List, Tuple, Optional, Any
from app.core.logging import logger

try:
    import ahocorasick
except Exception as e:
    logger.warning(f"pyahocorasick C-extension not available ({e}). Using pure Python dictionary fallback.")
    ahocorasick = None


class DictionaryAutomaton:
    """
    Quản lý Aho-Corasick Automaton cho việc chuẩn hóa từ ngữ nhanh chóng.
    Tự động fallback sang Pure-Python dictionary matching nếu thiếu pyahocorasick.
    """


    def __init__(self):
        self.automaton = None
        self.dictionary_map: Dict[str, str] = {}
        self.category_map: Dict[str, str] = {}
        self._is_built = False

    def load_dictionary(self, custom_dict: Optional[Dict[str, Tuple[str, str]]] = None):
        """
        Nạp từ điển mặc định và từ điển mở rộng.
        Dictionary Format: key -> (replacement, category)
        Categories: teencode, abbreviation, tech_term, typo
        """
        default_dict = {
            # Teencode
            "ko": ("không", "teencode"),
            "k": ("không", "teencode"),
            "khg": ("không", "teencode"),
            "đc": ("được", "teencode"),
            "dc": ("được", "teencode"),
            "mik": ("mình", "teencode"),
            "mn": ("mọi người", "teencode"),
            "bt": ("biết", "teencode"),
            "vd": ("ví dụ", "teencode"),
            # Common Typos
            "javscript": ("javascript", "typo"),
            "pyhton": ("python", "typo"),
            "reacjs": ("reactjs", "typo"),
            "dockerfile": ("Dockerfile", "tech_term"),
            # Tech Terms / Case normalization
            "dotnet": (".NET", "tech_term"),
            "js": ("JavaScript", "tech_term"),
            "ts": ("TypeScript", "tech_term"),
            "py": ("Python", "tech_term"),
        }

        if custom_dict:
            default_dict.update(custom_dict)

        self.dictionary_map = {}
        self.category_map = {}

        if ahocorasick is not None:
            self.automaton = ahocorasick.Automaton()
            for word, (replacement, category) in default_dict.items():
                self.automaton.add_word(word.lower(), (word, replacement, category))
                self.dictionary_map[word.lower()] = replacement
                self.category_map[word.lower()] = category
            self.automaton.make_automaton()
        else:
            self.automaton = None
            for word, (replacement, category) in default_dict.items():
                self.dictionary_map[word.lower()] = replacement
                self.category_map[word.lower()] = category

        self._is_built = True
        logger.info(f"Dictionary Automaton loaded with {len(default_dict)} patterns (Aho-Corasick: {ahocorasick is not None}).")


    def replace_all(self, text: str) -> Tuple[str, List[Dict[str, Any]], Dict[str, int]]:
        """
        Chuẩn hóa văn bản bằng Aho-Corasick.
        Trả về: (normalized_text, issues_found, category_counts)
        """
        if not self._is_built or not self.automaton:
            self.load_dictionary()

        # Tokenize theo ranh giới từ (word boundaries) để tránh thay thế nhầm nguyên cả từ dài hơn
        words = text.split(" ")
        normalized_words = []
        issues = []
        counts = {"teencode_count": 0, "typo_count": 0}

        for word in words:
            # Loại bỏ dấu câu quanh từ để check
            clean_word = word.strip(".,!?:;\"'()[]{}")
            lower_clean = clean_word.lower()

            if lower_clean in self.dictionary_map:
                replacement = self.dictionary_map[lower_clean]
                category = self.category_map.get(lower_clean, "general")

                # Thay thế từ trong word gốc
                new_word = word.replace(clean_word, replacement)
                normalized_words.append(new_word)

                if category == "teencode":
                    counts["teencode_count"] += 1
                elif category == "typo":
                    counts["typo_count"] += 1

                issues.append({
                    "type": category,
                    "original": clean_word,
                    "corrected": replacement,
                    "confidence": 1.0,
                    "message": f"Auto-replaced by Aho-Corasick ({category})"
                })
            else:
                normalized_words.append(word)

        return " ".join(normalized_words), issues, counts
