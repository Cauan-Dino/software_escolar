"""Cliente de LLM falso para os testes do assistente (respostas roteirizadas, sem rede)."""

import json
import uuid
from typing import Any

from app.modules.assistente.llm import LLMResponse, ToolCall


class FakeLLM:
    """Devolve as respostas na ordem em que foram roteirizadas e guarda cada chamada."""

    def __init__(self, respostas: list[LLMResponse]) -> None:
        self.respostas = list(respostas)
        self.chamadas: list[dict[str, Any]] = []

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> LLMResponse:
        self.chamadas.append({"messages": json.loads(json.dumps(messages)), "tools": tools})
        if not self.respostas:
            raise AssertionError("FakeLLM sem respostas roteirizadas restantes")
        return self.respostas.pop(0)

    @property
    def nomes_das_tools(self) -> set[str]:
        return {t["function"]["name"] for t in self.chamadas[0]["tools"]}

    def ultimas_mensagens_tool(self) -> list[dict[str, Any]]:
        return [m for m in self.chamadas[-1]["messages"] if m["role"] == "tool"]


def texto(conteudo: str) -> LLMResponse:
    return LLMResponse(content=conteudo)


def chamar(nome: str, content: str | None = None, **args: Any) -> LLMResponse:
    return LLMResponse(
        content=content,
        tool_calls=[
            ToolCall(id=f"call_{uuid.uuid4().hex[:8]}", name=nome, arguments=json.dumps(args))
        ],
    )


def chamar_varias(*chamadas: tuple[str, dict[str, Any]]) -> LLMResponse:
    return LLMResponse(
        content=None,
        tool_calls=[
            ToolCall(id=f"call_{uuid.uuid4().hex[:8]}", name=nome, arguments=json.dumps(args))
            for nome, args in chamadas
        ],
    )


def chamar_json_bruto(nome: str, bruto: str) -> LLMResponse:
    return LLMResponse(
        content=None, tool_calls=[ToolCall(id="call_raw", name=nome, arguments=bruto)]
    )
