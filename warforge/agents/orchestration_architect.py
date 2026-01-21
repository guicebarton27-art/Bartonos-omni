from __future__ import annotations

from warforge.agents.base import Agent, AgentResult


class OrchestrationArchitectAgent(Agent):
    name = "orchestration_architect"

    def run(self, context):
        workflow = {
            "pattern": "supervisor",
            "agents": [
                "router",
                "repo_analyst",
                "planner",
                "implementer",
                "test_engineer",
                "reviewer",
            ],
            "gates": [
                "plan_complete",
                "implementation_complete",
                "verification_complete",
            ],
            "tools": ["git", "package_manager", "provider"],
        }
        return AgentResult(name=self.name, payload=workflow)
