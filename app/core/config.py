import os
from typing import List, Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "QualityService"
    APP_ENV: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    LOG_LEVEL: str = "INFO"
    # MongoDB Config

    MONGODB_URL: str = "mongodb+srv://shopee-sentiment:MChau2506@cluster0.qlbix.mongodb.net/quality"
    MONGODB_DB_NAME: str = "quality"

    # Elasticsearch

    ELASTICSEARCH_ENABLED: bool = False
    ELASTICSEARCH_HOSTS: str = "http://localhost:9200"
    ELASTICSEARCH_INDEX: str = "typo_dictionary"
    ELASTICSEARCH_TIMEOUT: float = 2.0

    # Model Paths
    IT_MODEL_PATH: str = "app/models/saved/it_classifier.pkl"
    IT_VECTORIZER_PATH: str = "app/models/saved/it_vectorizer.pkl"
    TOXIC_MODEL_PATH: str = "app/models/saved/toxic_classifier.bin"
    TOXIC_PKL_MODEL_PATH: str = "app/models/saved/toxic_classifier.pkl"
    TOXIC_PKL_VECTORIZER_PATH: str = "app/models/saved/toxic_vectorizer.pkl"

    # Thresholds
    IT_THRESHOLD: float = 0.60
    TOXIC_SUSPICIOUS_THRESHOLD: float = 0.50
    TOXIC_HIGH_THRESHOLD: float = 0.80
    FUZZY_AUTO_REPLACE_THRESHOLD: float = 0.95
    FUZZY_CANDIDATE_THRESHOLD: float = 0.70

    # Scoring Weights
    WEIGHT_RELEVANCE: float = 0.25
    WEIGHT_READABILITY: float = 0.20
    WEIGHT_STRUCTURE: float = 0.20
    WEIGHT_SAFETY: float = 0.20
    WEIGHT_CONTENT_QUALITY: float = 0.15

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_scoring_weights(self) -> Dict[str, float]:
        weights = {
            "relevance": self.WEIGHT_RELEVANCE,
            "readability": self.WEIGHT_READABILITY,
            "structure": self.WEIGHT_STRUCTURE,
            "safety": self.WEIGHT_SAFETY,
            "content_quality": self.WEIGHT_CONTENT_QUALITY
        }
        total = sum(weights.values())
        if abs(total - 1.0) > 1e-4:
            # Normalize if slightly off
            weights = {k: v / total for k, v in weights.items()}
        return weights


settings = Settings()
