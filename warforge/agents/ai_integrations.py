from __future__ import annotations

from warforge.agents.base import Agent, AgentResult


class AIIntegrationsAgent(Agent):
    name = "ai_integrations"

    def run(self, context):
        adapters = ["openai", "openrouter", "local"]
        return AgentResult(
            name=self.name,
            payload={"adapters": adapters, "tool_calling": "strict", "schema": "warforge/templates/tool_schema.json"},
        )
