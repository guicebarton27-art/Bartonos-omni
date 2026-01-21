from __future__ import annotations

from warforge.agents.base import Agent, AgentResult


class TestEngineerAgent(Agent):
    name = "test_engineer"

    def run(self, context):
        commands = context.get("verification_commands", [])
        return AgentResult(
            name=self.name,
            payload={"status": "pending", "commands": commands, "notes": "Verification queued."},
        )
