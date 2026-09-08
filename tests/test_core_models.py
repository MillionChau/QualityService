import pytest
from app.schemas import (
    AnalyzeRequest,
    ToxicityResult,
    ArticleStatistics,
    QualityIssue,
    QualityResult,
    SafetyScores,
    SafetyClassification,
    ITRelevanceLabel,
    ITDomainLabel,
    ITRelevanceResult,
    ITDomainResult,
    CodeAnalysisResult,
    SemanticResult,
    DuplicateType,
    DuplicateAnalysisResult,
    TagExtractionItem,
    TagExtractionResult,
    TechnicalDepthResult,
    UserRankEnum,
    UserFeatureVector,
    UserScoreBreakdown,
    PromotionEligibility,
    UserReputationResult,
    DatasetSample,
    ModelMetrics,
    ModelMetadata,
)


def test_safety_schemas():
    scores = SafetyScores(safe=0.98, toxic=0.01, spam=0.01)
    classification = SafetyClassification(primary_label="safe", probability=0.98, scores=scores)
    assert classification.is_acceptable is True
    assert classification.scores.toxic == 0.01

    toxicity = ToxicityResult(label="safe", probability=0.98)
    assert toxicity.label == "safe"


def test_domain_schemas():
    relevance = ITRelevanceResult(label=ITRelevanceLabel.IT, probability=0.95, is_it=True)
    domain = ITDomainResult(label=ITDomainLabel.BACKEND, confidence=0.89)

    assert relevance.label == ITRelevanceLabel.IT
    assert domain.label == "BACKEND"


def test_code_analysis_schemas():
    code_res = CodeAnalysisResult(
        has_code=True,
        code_blocks_count=2,
        declared_languages=["python", "sql"],
        code_ratio=0.35
    )
    assert code_res.has_code is True
    assert "python" in code_res.declared_languages


def test_semantic_and_duplicate_schemas():
    sem = SemanticResult(embedding_model="devradar-embedding-v1", cluster_id="backend-devops")
    dup = DuplicateAnalysisResult(
        is_duplicate=False,
        duplicate_type=DuplicateType.ORIGINAL,
        lexical_similarity=0.1,
        semantic_similarity=0.2
    )
    assert sem.embedding_model == "devradar-embedding-v1"
    assert dup.duplicate_type == DuplicateType.ORIGINAL


def test_tag_extraction_schemas():
    tags = TagExtractionResult(
        suggested_tags=["FastAPI", "Docker", "Python"],
        details=[TagExtractionItem(tag_name="FastAPI", confidence=0.99, source="dictionary")]
    )
    assert len(tags.suggested_tags) == 3
    assert tags.details[0].tag_name == "FastAPI"


def test_technical_depth_schemas():
    depth = TechnicalDepthResult(
        score=0.85,
        terminology_density=0.7,
        specificity_score=0.9,
        explanation_quality=0.8,
        coherence_score=0.85,
        signals=["code_present", "high_terminology"]
    )
    assert depth.score == 0.85


def test_user_reputation_schemas():
    feature_vec = UserFeatureVector(content_quality=0.9, technical_contribution=0.85)
    breakdown = UserScoreBreakdown(content_quality_score=225.0, technical_contribution_score=170.0)
    promotion = PromotionEligibility(
        eligible=True,
        current_level=UserRankEnum.EXPERT,
        next_level=UserRankEnum.SENIOR
    )
    user_rep = UserReputationResult(
        user_id="usr_12345",
        user_score=680,
        rank=UserRankEnum.SENIOR,
        features=feature_vec,
        breakdown=breakdown,
        promotion=promotion
    )
    assert user_rep.user_score == 680
    assert user_rep.rank == UserRankEnum.SENIOR
    assert user_rep.promotion.eligible is True


def test_mlops_schemas():
    sample = DatasetSample(text="Học FastAPI cơ bản", is_it=True, domain="BACKEND")
    metrics = ModelMetrics(accuracy=0.94, f1=0.93)
    meta = ModelMetadata(
        model_name="it-classifier",
        version="v1.0.0",
        training_dataset_version="ds-v1",
        metrics=metrics
    )
    assert sample.is_it is True
    assert meta.metrics.accuracy == 0.94


def test_extended_quality_result_backward_compatibility():
    # Legacy QualityResult creation
    legacy_result = QualityResult(
        is_it=True,
        it_probability=0.95,
        toxicity=ToxicityResult(label="safe", probability=0.98),
        quality_score=88,
        quality_level="good",
        statistics=ArticleStatistics(word_count=50, sentence_count=3, paragraph_count=1),
        issues=[QualityIssue(type="teencode", original="mn", corrected="mọi người")]
    )
    assert legacy_result.is_it is True
    assert legacy_result.quality_score == 88
    assert legacy_result.toxicity.label == "safe"
    assert legacy_result.it_relevance is None

    # Extended QualityResult creation
    extended_result = QualityResult(
        is_it=True,
        it_probability=0.95,
        toxicity=ToxicityResult(label="safe", probability=0.98),
        quality_score=92,
        quality_level="excellent",
        statistics=ArticleStatistics(word_count=150),
        it_relevance=ITRelevanceResult(label=ITRelevanceLabel.IT, probability=0.95, is_it=True),
        domain=ITDomainResult(label=ITDomainLabel.BACKEND, confidence=0.91),
        suggested_tags=["FastAPI", "Python", "Docker"],
        technical_depth=TechnicalDepthResult(score=0.88)
    )
    assert extended_result.quality_score == 92
    assert "FastAPI" in extended_result.suggested_tags
    assert extended_result.domain.label == ITDomainLabel.BACKEND
