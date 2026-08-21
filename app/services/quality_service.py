from typing import Optional
from app.dictionary.aho_corasick import DictionaryAutomaton
from app.clients.elasticsearch_client import ElasticsearchClient
from app.models.it_classifier import ITDomainClassifier
from app.models.toxic_classifier import ToxicClassifier
from app.pipeline.cleaner import TextCleaner
from app.pipeline.normalizer import TextNormalizer
from app.pipeline.tokenizer import VietnameseTokenizer
from app.pipeline.classifier import ClassifierPipeline
from app.pipeline.quality_analyzer import QualityAnalyzerEngine
from app.pipeline.scorer import QualityScorer
from app.pipeline.pipeline import QualityPipeline
from app.schemas.quality import QualityResult
from app.core.logging import logger


class QualityService:
    def __init__(self):
        self.automaton = DictionaryAutomaton()
        self.es_client = ElasticsearchClient()
        self.it_classifier = ITDomainClassifier()
        self.toxic_classifier = ToxicClassifier()
        self.pipeline: Optional[QualityPipeline] = None

    def initialize(self):
        logger.info("Initializing QualityService singletons...")
        # 1. Load Aho-Corasick Automaton
        self.automaton.load_dictionary()

        # 2. Load ML Classifiers
        self.it_classifier.load_model()
        self.toxic_classifier.load_model()

        # 3. Assemble Pipeline
        cleaner = TextCleaner()
        normalizer = TextNormalizer(self.automaton, self.es_client)
        tokenizer = VietnameseTokenizer()
        classifier = ClassifierPipeline(self.it_classifier, self.toxic_classifier)
        analyzer = QualityAnalyzerEngine()
        scorer = QualityScorer()

        self.pipeline = QualityPipeline(
            cleaner=cleaner,
            normalizer=normalizer,
            tokenizer=tokenizer,
            classifier=classifier,
            analyzer=analyzer,
            scorer=scorer
        )
        logger.info("QualityService initialization complete.")

    def analyze_article(self, content: str) -> QualityResult:
        if not self.pipeline:
            self.initialize()
        return self.pipeline.process(content)


# Global Service Singleton
quality_service = QualityService()
