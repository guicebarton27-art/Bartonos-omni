from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Protocol


class Provider(Protocol):
    name: str

    def stream(self, prompt: str) -> Iterable[str]:
        ...

    def tool_call(self, tool_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        ...

    def cost(self) -> Dict[str, Any]:
        ...


@dataclass
class ProviderConfig:
    name: str
    base_url: str
    api_key_env: str


class StubProvider:
    name = "stub"

    def stream(self, prompt: str) -> Iterable[str]:
        yield "[stub] " + prompt

    def tool_call(self, tool_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"tool": tool_name, "payload": payload, "status": "ok"}

    def cost(self) -> Dict[str, Any]:
        return {"currency": "usd", "amount": 0}
