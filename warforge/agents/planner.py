from __future__ import annotations

from warforge.agents.base import Agent, AgentResult


class PlannerAgent(Agent):
    name = "planner"

    def run(self, context):
        plan = {
            "objective": context.get("title"),
            "done_checks": [
                "demo_pipeline_runs",
                "receipt_generated",
                "tests_pass",
            ],
            "milestones": [
                "analyze repo",
                "generate workflow",
                "implement changes",
                "run verification",
            ],
            "file_targets": ["README.md", "warforge/"],
            "rollback_plan": "Revert the run commit and restore artifacts from last green run.",
            "speed_plan": {
                "parallel_steps": ["repo_analysis", "doc_scan"],
                "cache": ["repo_index", "test_results"],
            },
        }
        return AgentResult(name=self.name, payload=plan)
