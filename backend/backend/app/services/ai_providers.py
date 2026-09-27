import os
import json
import logging
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv

logger = logging.getLogger("ai_academic_assistant")
MAX_PROVIDER_INPUT_CHARS = 14000


def _bound_provider_input(system_prompt: str, messages: List[Dict[str, str]]) -> Tuple[str, List[Dict[str, str]]]:
    """Keep provider requests below token-per-minute limits across all providers."""
    bounded_system = str(system_prompt or "")[:3000]
    bounded_messages = []
    remaining = MAX_PROVIDER_INPUT_CHARS - len(bounded_system)
    for message in reversed(messages):
        if remaining <= 0:
            break
        content = str(message.get("content", ""))[:min(5000, remaining)]
        bounded_messages.insert(0, {"role": message.get("role", "user"), "content": content})
        remaining -= len(content)
    return bounded_system, bounded_messages


def reload_environment():
    """Ensure latest .env variables are loaded."""
    current_file = Path(__file__).resolve()
    env_paths = [
        current_file.parents[2] / ".env",
        current_file.parents[3] / ".env",
        Path.cwd() / ".env"
    ]
    for p in env_paths:
        if p.exists():
            load_dotenv(p, override=True)


def _http_post_json(url: str, payload: dict, headers: dict = None, timeout: float = 30.0) -> Tuple[Optional[int], Optional[dict]]:
    """
    Zero-dependency HTTP POST JSON helper using Python standard library urllib.
    Includes browser-standard User-Agent to avoid Cloudflare 403 Error 1010.
    """
    req_headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }
    if headers:
        req_headers.update(headers)

    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data_bytes, headers=req_headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = response.status
            body = response.read().decode("utf-8")
            return status_code, json.loads(body)
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="ignore")
            logger.warning(f"HTTPError {e.code} for {url.split('?')[0]}: provider request failed")
        except Exception:
            logger.warning(f"HTTPError {e.code} for {url.split('?')[0]}")
        return e.code, None
    except Exception as e:
        logger.warning(f"Request error for {url.split('?')[0]}: {type(e).__name__}")
        return None, None


class BaseAIProvider:
    name: str = "base"

    def is_configured(self) -> bool:
        raise NotImplementedError

    def generate(self, system_prompt: str, messages: List[Dict[str, str]]) -> Optional[str]:
        raise NotImplementedError


class GroqProvider(BaseAIProvider):
    name = "Groq"

    @property
    def api_key(self) -> str:
        return os.getenv("GROQ_API_KEY", "").strip()

    @property
    def model(self) -> str:
        return os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()

    @property
    def base_url(self) -> str:
        return os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1/chat/completions").strip()

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate(self, system_prompt: str, messages: List[Dict[str, str]]) -> Optional[str]:
        if not self.is_configured():
            return None

        formatted_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            role = "assistant" if msg["role"] in ("assistant", "system_bot") else "user"
            formatted_messages.append({"role": role, "content": msg["content"]})

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": 0.5,
            "max_tokens": 600,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        status, data = _http_post_json(self.base_url, payload, headers=headers, timeout=25.0)
        if status == 200 and data:
            choices = data.get("choices", [])
            if choices and "message" in choices[0]:
                return choices[0]["message"].get("content", "").strip()
        return None


class GeminiProvider(BaseAIProvider):
    name = "Gemini"

    @property
    def api_key(self) -> str:
        return os.getenv("GEMINI_API_KEY", "").strip()

    @property
    def model(self) -> str:
        return os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate(self, system_prompt: str, messages: List[Dict[str, str]]) -> Optional[str]:
        if not self.is_configured():
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        contents = []
        for msg in messages:
            role = "model" if msg["role"] in ("assistant", "system_bot") else "user"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })

        payload = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": 0.5,
                "maxOutputTokens": 1024
            }
        }

        status, data = _http_post_json(url, payload, timeout=25.0)
        if status == 200 and data:
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts and "text" in parts[0]:
                    return parts[0]["text"].strip()
        return None


class HuggingFaceProvider(BaseAIProvider):
    name = "Hugging Face"

    @property
    def api_key(self) -> str:
        return os.getenv("HUGGINGFACE_API_KEY", "").strip()

    @property
    def model(self) -> str:
        return os.getenv("HUGGINGFACE_MODEL", "meta-llama/Llama-3.1-8B-Instruct").strip()

    @property
    def base_url(self) -> str:
        return os.getenv("HUGGINGFACE_BASE_URL", "https://router.huggingface.co/novita/v1/chat/completions").strip()

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate(self, system_prompt: str, messages: List[Dict[str, str]]) -> Optional[str]:
        if not self.is_configured():
            return None

        formatted_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            role = "assistant" if msg["role"] in ("assistant", "system_bot") else "user"
            formatted_messages.append({"role": role, "content": msg["content"]})

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": 0.5,
            "max_tokens": 1024,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        status, data = _http_post_json(self.base_url, payload, headers=headers, timeout=30.0)
        if status == 200 and data:
            choices = data.get("choices", [])
            if choices and "message" in choices[0]:
                return choices[0]["message"].get("content", "").strip()

        # Fallback to direct inference endpoint if router format differs
        legacy_url = f"https://api-inference.huggingface.co/models/{self.model}/v1/chat/completions"
        status_leg, data_leg = _http_post_json(legacy_url, payload, headers=headers, timeout=30.0)
        if status_leg == 200 and data_leg:
            choices = data_leg.get("choices", [])
            if choices and "message" in choices[0]:
                return choices[0]["message"].get("content", "").strip()
        return None


class OllamaProvider(BaseAIProvider):
    name = "Ollama"

    @property
    def base_url(self) -> str:
        return os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")

    @property
    def model(self) -> str:
        return os.getenv("OLLAMA_MODEL", "").strip()

    @property
    def timeout(self) -> float:
        try:
            # A locally loaded model can need time to recover from another
            # model (for example an 8B model) being evicted from memory.
            return max(10.0, float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "90")))
        except ValueError:
            return 90.0

    @property
    def keep_alive(self) -> str:
        return os.getenv("OLLAMA_KEEP_ALIVE", "15m").strip() or "15m"

    @property
    def max_tokens(self) -> int:
        try:
            return min(2048, max(64, int(os.getenv("OLLAMA_MAX_TOKENS", "768"))))
        except ValueError:
            return 768

    def is_configured(self) -> bool:
        return bool(self.model)

    def generate(self, system_prompt: str, messages: List[Dict[str, str]]) -> Optional[str]:
        if not self.is_configured():
            return None

        formatted_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            role = "assistant" if msg["role"] in ("assistant", "system_bot") else "user"
            formatted_messages.append({"role": role, "content": msg["content"]})

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "stream": False,
            "keep_alive": self.keep_alive,
            "options": {
                "temperature": 0.6,
                "num_predict": self.max_tokens,
            }
        }

        # Try the standard Ollama endpoint first. A failed local model should
        # fall through quickly to the database-backed response engine.
        url = f"{self.base_url}/api/chat"
        status, data = _http_post_json(url, payload, timeout=self.timeout)
        if status == 200 and data:
            msg = data.get("message", {})
            if "content" in msg:
                return msg["content"].strip()

        # Only try the compatibility endpoint when the standard endpoint is
        # explicitly unavailable; do not double the wait after a model timeout.
        if status not in (404, 405):
            if status is None:
                logger.warning("Ollama did not answer within %.0f seconds; it may be loading or busy with another model.", self.timeout)
            return None
        v1_url = f"{self.base_url}/v1/chat/completions"
        status_v1, data_v1 = _http_post_json(v1_url, payload, timeout=self.timeout)
        if status_v1 == 200 and data_v1:
            choices = data_v1.get("choices", [])
            if choices and "message" in choices[0]:
                return choices[0]["message"].get("content", "").strip()

        return None



class AIProviderManager:
    def __init__(self):
        self.providers: List[BaseAIProvider] = [
            GroqProvider(),
            GeminiProvider(),
            HuggingFaceProvider(),
            OllamaProvider(),
        ]

    def get_configured_providers(self) -> List[str]:
        reload_environment()
        return [p.name for p in self.providers if p.is_configured()]

    def generate_chat(self, system_prompt: str, messages: List[Dict[str, str]], response_validator=None) -> Tuple[Optional[str], Optional[str]]:
        """
        Attempts to generate response from providers in sequence:
        Groq -> Gemini -> Hugging Face -> Ollama
        Returns (response_text, provider_name) or (None, None) if all fail.
        """
        reload_environment()
        system_prompt, messages = _bound_provider_input(system_prompt, messages)
        for provider in self.providers:
            if not provider.is_configured():
                continue
            logger.info(f"Connecting to AI provider: {provider.name} (model: {getattr(provider, 'model', 'default')})")
            print(f"[AI Assistant] Routing question to: {provider.name} ({getattr(provider, 'model', 'default')})")
            try:
                response = provider.generate(system_prompt, messages)
                if response:
                    if response_validator is not None:
                        # Timetable structured plans can reject malformed content
                        # and continue through the same provider chain.
                        response_validator(response)
                    print(f"[AI Assistant] Successfully generated response via {provider.name}")
                    return response, provider.name
                else:
                    print(f"[AI Assistant] Provider {provider.name} returned empty response or error, trying next...")
            except Exception as exc:
                logger.error(f"Provider {provider.name} failed with error: {exc}")
                print(f"[AI Assistant] Provider {provider.name} failed: {exc}")
                continue

        return None, None
