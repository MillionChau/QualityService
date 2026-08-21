from typing import Tuple, List, Dict, Any
from app.dictionary.aho_corasick import DictionaryAutomaton
from app.clients.elasticsearch_client import ElasticsearchClient
from app.core.config import settings


class TextNormalizer:
    def __init__(self, automaton: DictionaryAutomaton, es_client: ElasticsearchClient):
        self.automaton = automaton
        self.es_client = es_client

    def normalize(self, text: str) -> Tuple[str, List[Dict[str, Any]], Dict[str, int]]:
        """
        1. Aho-Corasick replacement (Fast exact match).
        2. Elasticsearch fuzzy search fallback cho những từ chưa tìm thấy.
        """
        # Step 1: Aho-Corasick
        normalized_text, issues, counts = self.automaton.replace_all(text)

        # Step 2: Fuzzy lookup cho từ nghi ngờ nếu Elasticsearch được bật
        if self.es_client.enabled:
            words = normalized_text.split(" ")
            new_words = []
            for word in words:
                clean_word = word.strip(".,!?:;\"'()[]{}")
                if len(clean_word) > 4 and not clean_word.startswith("[["):

                    candidate, confidence = self.es_client.fuzzy_search_term(clean_word)
                    if candidate and confidence >= settings.FUZZY_AUTO_REPLACE_THRESHOLD:
                        new_word = word.replace(clean_word, candidate)
                        new_words.append(new_word)
                        counts["typo_count"] += 1
                        issues.append({
                            "type": "spelling",
                            "original": clean_word,
                            "corrected": candidate,
                            "confidence": confidence,
                            "message": f"Auto-replaced by Elasticsearch Fuzzy (> {settings.FUZZY_AUTO_REPLACE_THRESHOLD})"
                        })
                    elif candidate and confidence >= settings.FUZZY_CANDIDATE_THRESHOLD:
                        new_words.append(word)
                        issues.append({
                            "type": "spelling_candidate",
                            "original": clean_word,
                            "corrected": candidate,
                            "confidence": confidence,
                            "message": f"Suggested candidate by Elasticsearch Fuzzy ({settings.FUZZY_CANDIDATE_THRESHOLD} - {settings.FUZZY_AUTO_REPLACE_THRESHOLD})"
                        })
                    else:
                        new_words.append(word)
                else:
                    new_words.append(word)
            normalized_text = " ".join(new_words)

        return normalized_text, issues, counts
