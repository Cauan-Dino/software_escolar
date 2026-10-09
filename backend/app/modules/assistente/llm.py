"""Cliente do LLM (DeepSeek, API compatível com OpenAI) por trás de uma interface mínima.

O service só conhece `LLMClient`; os testes usam um cliente falso com respostas roteirizadas,
então nenhum teste chama a rede.
"""

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Protocol

from app.core.config import settings
from app.core.exceptions import AppError

logger = logging.getLogger(__name__)

TEMPERATURA = 0.2


class LLMIndisponivelError(AppError):
    status_code = 502
    default_code = "LLM_INDISPONIVEL"
    default_detail = "O assistente está indisponível no momento. Tente novamente em instantes."


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: str  # JSON em texto, exatamente como o modelo devolveu


@dataclass(frozen=True)
class LLMResponse:
    content: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)


class LLMClient(Protocol):
    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> LLMResponse: ...


class DeepSeekClient:
    """Chama `POST {base_url}/chat/completions` (formato OpenAI) só com a biblioteca padrão."""

    def __init__(self, *, api_key: str, base_url: str, model: str, timeout: float) -> None:
        self._api_key = api_key
        self._url = f"{base_url.rstrip('/')}/chat/completions"
        self._model = model
        self._timeout = timeout

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> LLMResponse:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": TEMPERATURA,
        }
        if tools:
            payload["tools"] = tools
        request = urllib.request.Request(  # noqa: S310 (URL vem da configuração, https)
            self._url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as resp:  # noqa: S310
                corpo = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detalhe = exc.read().decode("utf-8", errors="replace")[:500]
            logger.warning("LLM respondeu %s: %s", exc.code, detalhe)
            raise LLMIndisponivelError() from exc
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            logger.warning("Falha ao chamar o LLM: %s", exc)
            raise LLMIndisponivelError() from exc
        return parse_response(corpo)


def parse_response(corpo: dict[str, Any]) -> LLMResponse:
    choices = corpo.get("choices") or []
    if not choices:
        raise LLMIndisponivelError()
    message = choices[0].get("message") or {}
    calls = [
        ToolCall(
            id=c.get("id") or f"call_{i}",
            name=c["function"]["name"],
            arguments=c["function"].get("arguments") or "{}",
        )
        for i, c in enumerate(message.get("tool_calls") or [])
        if c.get("type", "function") == "function" and c.get("function", {}).get("name")
    ]
    return LLMResponse(content=message.get("content") or None, tool_calls=calls)


def build_default_client() -> LLMClient:
    return DeepSeekClient(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_model,
        timeout=settings.deepseek_timeout_seconds,
    )
