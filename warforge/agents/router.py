from __future__ import annotations

from warforge.agents.base import Agent, AgentResult


class RouterAgent(Agent):
    name = "router"

    def run(self, context):
        description = context.get("description", "").lower()
        task_type = "feature"
        if "bug" in description:
            task_type = "bugfix"
        if "infra" in description or "deploy" in description:
            task_type = "infra"
        if "bot" in description:
            task_type = "bot"
        if "eval" in description or "test" in description:
            task_type = "eval"
        policy = "safe" if context.get("safe_mode", True) else "fast"
        workflow = "supervisor"
        if task_type in {"bot", "eval"}:
            workflow = "swarm"
        return AgentResult(
            name=self.name,
            payload={"task_type": task_type, "policy": policy, "workflow_template": workflow},
        )
