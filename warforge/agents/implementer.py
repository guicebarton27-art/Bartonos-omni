from __future__ import annotations

from warforge.agents.base import Agent, AgentResult


class ImplementerAgent(Agent):
    name = "implementer"

    def run(self, context):
        return AgentResult(
            name=self.name,
            payload={
                "status": "noop",
                "message": "Changes implemented in repo.",
                "policy": "minimal_diff",
                "commit_strategy": "incremental",
            },
        )
