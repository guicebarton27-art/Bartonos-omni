from __future__ import annotations

from warforge.agents.base import Agent, AgentResult


class BotsAutomationAgent(Agent):
    name = "bots_automation"

    def run(self, context):
        templates = [
            "monitoring_bot",
            "alert_bot",
            "recovery_bot",
            "data_pipeline_bot",
            "integration_bot",
        ]
        return AgentResult(name=self.name, payload={"templates": templates})
