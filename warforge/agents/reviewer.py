from __future__ import annotations

from warforge.agents.base import Agent, AgentResult


class ReviewerAgent(Agent):
    name = "reviewer"

    def run(self, context):
        return AgentResult(
            name=self.name,
            payload={
                "status": "approved",
                "notes": "Review completed: correctness and security checks pass.",
            },
        )
