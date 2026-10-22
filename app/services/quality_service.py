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


from app.clients.mongo_client import mongo_client
from app.clients.llm_client import llm_client
from app.core.config import settings
from app.api.routes.ai_assistant import _extract_json_from_llm


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

    async def analyze_article(self, content: str, content_type: str = "post") -> QualityResult:
        if not self.pipeline:
            self.initialize()
        result = self.pipeline.process(content, content_type=content_type)

        # Với bình luận (comment), tiêu chí hợp lệ chủ yếu là an toàn (không cần là bài viết IT dài)
        if content_type.lower() == "comment":
            result.is_valid = (result.toxicity.label == "safe")

        # Thẩm định chéo an toàn nội dung bằng External LLM (UnoRouter) nếu có cấu hình
        # Tối ưu hóa hiệu năng & quota:
        # 1. Nếu pipeline local đã phân loại chắc chắn là 'toxic', không cần chờ LLM (tránh độ trễ).
        # 2. Nếu là bài viết (post) mà local model đã xác định KHÔNG PHẢI IT (is_it == False) hoặc điểm quá thấp (< 35),
        #    bài viết đã không hợp lệ, KHÔNG CẦN gọi External LLM (tiết kiệm quota 1 req/min và tránh nguy cơ timeout).
        # 3. Chỉ gọi External LLM khi cần thẩm định an toàn chéo cho nội dung nghi ngờ hoặc đạt chuẩn IT ban đầu.
        should_call_llm = (
            llm_client.is_available()
            and result.toxicity.label == "suspicious"
        )
        if should_call_llm:
            try:
                if content_type.lower() == "comment":
                    system_prompt = (
                        "Bạn là Hệ thống Kiểm duyệt AI (AI Content Safety Moderator) của mạng xã hội DevRadar. "
                        "Nhiệm vụ: Đánh giá bình luận sau có vi phạm tiêu chuẩn an toàn (chửi bới thô tục, xúc phạm, toxic, thù địch, quấy rối, spam rác, lừa đảo, đồi trụy) hay không. "
                        "CHÚ Ý ĐẶC BIỆT: Đối với bình luận (comment), KHÔNG yêu cầu phải có nội dung chuyên ngành CNTT (người dùng có thể cảm ơn, chào hỏi, khen ngợi, hỏi han...). "
                        "Chỉ đánh giá xem bình luận có an toàn hay độc hại (toxicity). "
                        "BẮT BUỘC chỉ trả về kết quả định dạng JSON: "
                        '{"is_safe": true, "toxicity": "safe", "reason": "Nội dung an toàn"}'
                    )
                else:
                    system_prompt = (
                        "Bạn là Hệ thống Kiểm duyệt AI (AI Content Safety Moderator) của mạng xã hội DevRadar. "
                        "Nhiệm vụ: Đánh giá xem đoạn văn bản sau có vi phạm tiêu chuẩn cộng đồng (chửi bới thô tục, xúc phạm, toxic, thù địch, quấy rối, spam rác, lừa đảo, đồi trụy) hay không. "
                        "BẮT BUỘC chỉ trả về kết quả định dạng JSON: "
                        '{"is_safe": true, "toxicity": "safe", "reason": "Nội dung an toàn"}'
                    )
                user_prompt = f"Loại nội dung: {content_type}\nNội dung cần kiểm duyệt:\n\"\"\"{content.strip()}\"\"\""
                raw_llm = await llm_client.generate_text(system_prompt, user_prompt, temperature=0.1, max_tokens=250)
                parsed = _extract_json_from_llm(raw_llm) if raw_llm else None

                if parsed:
                    is_safe = parsed.get("is_safe", True)
                    tox = str(parsed.get("toxicity", "safe")).lower()
                    reason = str(parsed.get("reason", "Nội dung an toàn"))

                    result.ai_verified = True
                    result.llm_model = settings.AI_MODEL
                    result.moderation_reason = reason

                    if not is_safe or tox in ["toxic", "spam", "suspicious"]:
                        result.is_valid = False
                        result.toxicity.label = tox
                        logger.warning(f"AI LLM ({settings.AI_MODEL}) flagged content as {tox}: {reason}")
            except Exception as e:
                logger.warning(f"Error during AI LLM moderation check: {e}. Falling back to pipeline result.")

        # Đảm bảo tuyệt đối: Bình luận (comment) KHÔNG cần check NonIT, chỉ cần toxicity là safe
        if content_type.lower() == "comment":
            result.is_valid = (result.toxicity.label == "safe")

        # Trích xuất và lưu vào MongoDB Atlas ('quality_results')
        if mongo_client.db is not None:
            try:
                await mongo_client.db["quality_results"].insert_one(result.model_dump())
                logger.info("Successfully saved QualityResult into MongoDB Atlas ('quality_results' collection).")
            except Exception as e:
                logger.warning(f"Failed to save QualityResult to MongoDB Atlas: {e}")

        return result


# Global Service Singleton
quality_service = QualityService()

