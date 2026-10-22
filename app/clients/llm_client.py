import json
from typing import List, Dict, Any, Optional
import httpx
from app.core.config import settings
from app.core.logging import logger


class LLMClient:
    """
    Client kết nối đến mô hình AI ngôn ngữ lớn (LLM Gateway) thông qua UnoRouter
    (chuẩn giao thức OpenAI-compatible API) với cơ chế Graceful Fallback an toàn.
    """

    def __init__(self):
        self.base_url = settings.AI_BASE_URL.rstrip("/")
        self.api_key = settings.AI_API_KEY
        self.model = settings.AI_MODEL
        self.timeout = min(settings.AI_TIMEOUT_SECONDS, 3.5)
        self.enabled = settings.EXTERNAL_AI_ENABLED

    def is_available(self) -> bool:
        """Kiểm tra cờ kích hoạt và khóa API có khả dụng không."""
        return bool(self.enabled and self.api_key and self.api_key.strip())

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1200
    ) -> Optional[str]:
        """
        Gửi yêu cầu chat completion đến UnoRouter.
        Trả về chuỗi văn bản phản hồi từ Assistant nếu thành công; trả về None nếu lỗi/timeout.
        """
        if not self.is_available():
            logger.debug("External LLM is disabled or AI_API_KEY is missing. Skipping LLM call.")
            return None

        endpoint = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(endpoint, json=payload, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    if choices and "message" in choices[0]:
                        content = choices[0]["message"].get("content", "").strip()
                        if content:
                            return content

                logger.warning(
                    f"UnoRouter LLM API returned status {res.status_code}: {res.text[:200]}. Falling back to heuristic."
                )
                return None
        except httpx.TimeoutException:
            logger.warning(f"UnoRouter LLM API timed out after {self.timeout}s. Gracefully falling back to heuristic.")
            return None
        except Exception as e:
            logger.warning(f"UnoRouter LLM API call failed ({e}). Gracefully falling back to heuristic.")
            return None

    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1200
    ) -> Optional[str]:
        """Tiện ích tạo văn bản từ cặp System Prompt và User Prompt."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return await self.chat_completion(messages, temperature=temperature, max_tokens=max_tokens)


llm_client = LLMClient()
