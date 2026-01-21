from __future__ import annotations

from warforge.agents.base import Agent, AgentResult


class EvalQualityAgent(Agent):
    name = "eval_quality"

    def run(self, context):
        return AgentResult(
            name=self.name,
            payload={"evals": ["smoke", "prompt", "golden"], "status": "ready"},
        )
