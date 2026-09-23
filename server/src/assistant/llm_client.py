"""
LLM Client — TrustShare AI Assistant

Multi-provider wrapper supporting:
- Groq (OpenAI-compatible)
- Google Gemini (OpenAI-compatible endpoint)
- Ollama (local, OpenAI-compatible)
- Any other OpenAI-compatible API
"""

import json
import logging
import time
from typing import Any, Optional

import httpx
from sqlalchemy.orm import Session

from src.assistant import config_service

logger = logging.getLogger(__name__)


class LLMError(Exception):
    pass


class LLMNotConfiguredError(LLMError):
    pass


class LLMAPIError(LLMError):
    pass


PROVIDER_BASE_URLS = {
    "groq": "https://api.groq.com/openai/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
    "ollama": "http://localhost:11434/v1",
    "openrouter": "https://openrouter.ai/api/v1",
}

PROVIDERS_REQUIRING_KEY = {"groq", "gemini", "openrouter"}


class LLMClient:

    def __init__(self, db: Session):
        self.db = db
        self._load_config()

    def _load_config(self):

        self.provider = config_service.get_str(self.db, "LLM_PROVIDER", "groq").lower()
        self.api_key = config_service.get(self.db, "LLM_API_KEY")
        self.model = config_service.get_str(
            self.db, "LLM_MODEL", "llama-3.3-70b-versatile"
        )
        self.max_tokens = config_service.get_int(self.db, "LLM_MAX_TOKENS", 1024)
        self.temperature = config_service.get_float(self.db, "LLM_TEMPERATURE", 0.7)
        self.timeout = config_service.get_int(self.db, "LLM_TIMEOUT_SECONDS", 30)

        db_base_url = config_service.get_str(self.db, "LLM_BASE_URL", "")
        self.base_url = db_base_url or PROVIDER_BASE_URLS.get(
            self.provider,
            "https://api.groq.com/openai/v1",
        )

    def is_configured(self) -> bool:

        if self.provider == "ollama":
            return bool(self.base_url)

        return bool(self.api_key)

    def _get_headers(self) -> dict:
        """Get provider-specific request headers."""
        headers = {"Content-Type": "application/json"}

        if self.provider == "ollama":
            return headers

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers

    def chat_completion(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> dict:

        if not self.is_configured():
            raise LLMNotConfiguredError(
                f"LLM provider '{self.provider}' is not properly configured. "
                f"{'Please install Ollama and pull a model.' if self.provider == 'ollama' else 'Configure API key via admin panel.'}"
            )

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        headers = self._get_headers()

        start = time.time()
        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            elapsed_ms = int((time.time() - start) * 1000)

            if response.status_code != 200:
                error_body = response.text[:500]
                logger.error(
                    f"LLM API error {response.status_code} from {self.provider}: {error_body}"
                )
                raise LLMAPIError(
                    f"LLM API returned {response.status_code}: {error_body}"
                )

            data = response.json()
            choice = data["choices"][0]
            message = choice["message"]

            return {
                "content": message.get("content"),
                "tool_calls": message.get("tool_calls") or [],
                "tokens_used": data.get("usage", {}).get("total_tokens", 0),
                "model_used": data.get("model", self.model),
                "elapsed_ms": elapsed_ms,
                "finish_reason": choice.get("finish_reason"),
                "provider": self.provider,
            }

        except httpx.TimeoutException:
            logger.error(f"{self.provider} request timed out after {self.timeout}s")
            raise LLMAPIError(
                f"{self.provider.capitalize()} request timed out after {self.timeout} seconds"
            )

        except httpx.ConnectError as e:
            logger.error(f"Cannot reach {self.provider}: {e}")
            if self.provider == "ollama":
                raise LLMAPIError(
                    "Cannot reach Ollama. Make sure Ollama is running: "
                    "run 'ollama serve' in terminal, or install from ollama.com"
                )
            raise LLMAPIError(
                f"Cannot reach {self.provider} API. Check your internet connection."
            )

        except LLMAPIError:
            raise

        except Exception as e:
            logger.error(
                f"Unexpected {self.provider} error: {type(e).__name__}: {e}",
                exc_info=True,
            )
            raise LLMAPIError(f"Unexpected error: {type(e).__name__}")

    def generate_conversation_title(self, first_user_message: str) -> str:

        from src.assistant import config_service
        from src.entities.assistant_prompt import AssistantPrompt

        max_length = config_service.get_int(self.db, "LLM_TITLE_MAX_LENGTH", 100)

        if not self.is_configured():
            return first_user_message[: max_length // 2]

        def _get_prompt(key: str, fallback: str) -> str:
            row = (
                self.db.query(AssistantPrompt)
                .filter(
                    AssistantPrompt.prompt_key == key, AssistantPrompt.is_active == True
                )
                .first()
            )
            return row.prompt_text if row else fallback

        system_prompt = _get_prompt(
            "TITLE_GENERATION_SYSTEM",
            "You generate a short 3-5 word title for a chat conversation. "
            "Return ONLY the title, no quotes, no punctuation, no explanation.",
        )
        user_prompt_template = _get_prompt(
            "TITLE_GENERATION_USER",
            "Generate a title for this message: {message}",
        )
        user_prompt = user_prompt_template.replace("{message}", first_user_message)

        try:
            result = self.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=20,
            )
            title = (result.get("content") or "").strip().strip('"').strip("'")
            return (
                title[:max_length] if title else first_user_message[: max_length // 2]
            )
        except Exception as e:
            logger.warning(f"Title generation failed: {e}")
            return first_user_message[: max_length // 2]
