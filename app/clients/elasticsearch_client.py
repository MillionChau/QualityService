from typing import Optional, Tuple
from app.core.config import settings
from app.core.logging import logger


class ElasticsearchClient:
    def __init__(self):
        self.enabled = settings.ELASTICSEARCH_ENABLED
        self.client = None
        if self.enabled:
            try:
                from elasticsearch import Elasticsearch
                self.client = Elasticsearch(
                    settings.ELASTICSEARCH_HOSTS,
                    request_timeout=settings.ELASTICSEARCH_TIMEOUT
                )
                logger.info("Elasticsearch Client initialized.")
            except Exception as e:
                logger.warning(f"Failed to initialize Elasticsearch client: {e}. Falling back to disabled.")
                self.enabled = False

    def fuzzy_search_term(self, word: str) -> Tuple[Optional[str], float]:
        """
        Thực hiện fuzzy search trên Elasticsearch index.
        Trả về (candidate_replacement, score_confidence).
        Nếu không bật hoặc có lỗi, trả về (None, 0.0).
        """
        if not self.enabled or not self.client:
            return None, 0.0

        try:
            response = self.client.search(
                index=settings.ELASTICSEARCH_INDEX,
                query={
                    "match": {
                        "term": {
                            "query": word,
                            "fuzziness": "AUTO"
                        }
                    }
                },
                size=1
            )
            hits = response.get("hits", {}).get("hits", [])
            if hits:
                best_match = hits[0]
                score = best_match.get("_score", 0.0)
                max_score = response.get("hits", {}).get("max_score", 1.0) or 1.0
                confidence = min(score / max_score, 1.0)
                corrected_word = best_match.get("_source", {}).get("corrected_term")
                return corrected_word, confidence
        except Exception as e:
            logger.warning(f"Elasticsearch search failed for word '{word}': {e}")

        return None, 0.0

    def health(self) -> dict:
        if not self.enabled or not self.client:
            return {"status": "disabled", "reachable": False}
        try:
            info = self.client.info()
            return {"status": "connected", "reachable": True, "version": info.get("version", {}).get("number")}
        except Exception as e:
            return {"status": "error", "reachable": False, "error": str(e)}
