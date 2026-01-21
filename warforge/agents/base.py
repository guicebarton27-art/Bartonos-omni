from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class AgentResult:
    name: str
    payload: Dict[str, Any]


class Agent:
    name: str = "agent"

    def run(self, context: Dict[str, Any]) -> AgentResult:
        raise NotImplementedError
