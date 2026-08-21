from fastapi import APIRouter
from app.schemas.quality import HealthCheckResponse
from app.services.quality_service import quality_service
from app.core.config import settings

router = APIRouter(prefix="/api/v1/quality", tags=["System Health"])


@router.get("/health", response_model=HealthCheckResponse, summary="Kiểm tra trạng thái dịch vụ")
async def health_check():
    es_health = quality_service.es_client.health()
    return HealthCheckResponse(
        status="healthy",
        service=settings.APP_NAME,
        env=settings.APP_ENV,
        components={
            "elasticsearch": es_health,
            "it_classifier_loaded": quality_service.it_classifier.loaded,
            "toxic_classifier_loaded": quality_service.toxic_classifier.loaded,
            "dictionary_automaton": quality_service.automaton._is_built
        }
    )


@router.get("/models", summary="Trạng thái các mô hình ML")
async def models_status():
    return {
        "it_classifier": {
            "loaded": quality_service.it_classifier.loaded,
            "threshold": settings.IT_THRESHOLD,
            "model_path": settings.IT_MODEL_PATH
        },
        "toxic_classifier": {
            "loaded": quality_service.toxic_classifier.loaded,
            "suspicious_threshold": settings.TOXIC_SUSPICIOUS_THRESHOLD,
            "high_threshold": settings.TOXIC_HIGH_THRESHOLD,
            "model_path": settings.TOXIC_MODEL_PATH
        }
    }


@router.get("/dictionary/status", summary="Trạng thái từ điển chuẩn hóa")
async def dictionary_status():
    return {
        "automaton_built": quality_service.automaton._is_built,
        "patterns_count": len(quality_service.automaton.dictionary_map),
        "elasticsearch_enabled": quality_service.es_client.enabled,
        "fuzzy_auto_threshold": settings.FUZZY_AUTO_REPLACE_THRESHOLD,
        "fuzzy_candidate_threshold": settings.FUZZY_CANDIDATE_THRESHOLD
    }
