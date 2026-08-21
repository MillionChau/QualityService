import re
import time
from typing import Dict, Any
from app.pipeline.cleaner import TextCleaner
from app.pipeline.normalizer import TextNormalizer
from app.pipeline.tokenizer import VietnameseTokenizer
from app.pipeline.classifier import ClassifierPipeline
from app.pipeline.quality_analyzer import QualityAnalyzerEngine
from app.pipeline.scorer import QualityScorer
from app.schemas.quality import QualityResult, ToxicityResult, ArticleStatistics, QualityIssue
from app.core.logging import logger


class QualityPipeline:
    def __init__(
        self,
        cleaner: TextCleaner,
        normalizer: TextNormalizer,
        tokenizer: VietnameseTokenizer,
        classifier: ClassifierPipeline,
        analyzer: QualityAnalyzerEngine,
        scorer: QualityScorer
    ):
        self.cleaner = cleaner
        self.normalizer = normalizer
        self.tokenizer = tokenizer
        self.classifier = classifier
        self.analyzer = analyzer
        self.scorer = scorer

    def process(self, content: str) -> QualityResult:
        start_time = time.time()
        logger.info("Starting Quality Pipeline execution...")

        # Stage 1: Text Cleaner & Content Protection
        cleaned_text, protected_map, cleaner_counts = self.cleaner.clean(content)

        # Stage 2: Normalization (Aho-Corasick + Elasticsearch Fuzzy)
        normalized_text, norm_issues, norm_counts = self.normalizer.normalize(cleaned_text)

        # Stage 3: Word Segmentation (Underthesea)
        segmented_text = self.tokenizer.tokenize(normalized_text)

        # Trích xuất thống kê bài viết
        restored_text = self.cleaner.restore(normalized_text, protected_map)
        paragraphs = [p for p in restored_text.split("\n\n") if p.strip()]
        sentences = [s for s in re.split(r"[.!?]+", restored_text) if s.strip()]
        words = restored_text.split()

        statistics = ArticleStatistics(
            word_count=len(words),
            sentence_count=len(sentences),
            paragraph_count=len(paragraphs),
            code_blocks=cleaner_counts.get("code_blocks", 0),
            urls=cleaner_counts.get("urls", 0),
            emoji_count=cleaner_counts.get("emoji_count", 0),
            teencode_count=norm_counts.get("teencode_count", 0),
            typo_count=norm_counts.get("typo_count", 0)
        )

        # Stage 4: Machine Learning Classification
        classification_res = self.classifier.classify(segmented_text)

        # Stage 5: Rule-based Quality Analysis
        analysis_res = self.analyzer.analyze(restored_text, statistics.model_dump(), protected_map)

        # Tổng hợp danh sách issues từ Normalization và Rule Engine
        all_issues = []
        for issue_dict in norm_issues + analysis_res.get("issues", []):
            all_issues.append(QualityIssue(**issue_dict))

        # Stage 6: Quality Scorer
        score, level = self.scorer.calculate_score(
            classification_res,
            analysis_res,
            statistics.model_dump()
        )

        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(f"Quality Pipeline completed in {elapsed_ms}ms. Final Score: {score} ({level})")

        return QualityResult(
            is_it=classification_res["is_it"],
            it_probability=classification_res["it_probability"],
            toxicity=ToxicityResult(**classification_res["toxicity"]),
            quality_score=score,
            quality_level=level,
            statistics=statistics,
            issues=all_issues,
            cleaned_text=restored_text
        )
