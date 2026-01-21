from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from warforge.agents.ai_integrations import AIIntegrationsAgent
from warforge.agents.bots_automation import BotsAutomationAgent
from warforge.agents.eval_quality import EvalQualityAgent
from warforge.agents.implementer import ImplementerAgent
from warforge.agents.ops_observability import OpsObservabilityAgent
from warforge.agents.orchestration_architect import OrchestrationArchitectAgent
from warforge.agents.planner import PlannerAgent
from warforge.agents.repo_analyst import RepoAnalystAgent
from warforge.agents.reviewer import ReviewerAgent
from warforge.agents.router import RouterAgent
from warforge.agents.test_engineer import TestEngineerAgent
from warforge.core import (
    RunContext,
    clock_ms,
    hash_files,
    human_duration_ms,
    now_iso,
    repo_files,
    write_json,
)
from warforge.policy import evaluate_policy
from warforge.verification import detect_verification_commands


AGENT_REGISTRY = {
    "router": RouterAgent,
    "repo_analyst": RepoAnalystAgent,
    "orchestration_architect": OrchestrationArchitectAgent,
    "planner": PlannerAgent,
    "implementer": ImplementerAgent,
    "test_engineer": TestEngineerAgent,
    "reviewer": ReviewerAgent,
    "ai_integrations": AIIntegrationsAgent,
    "bots_automation": BotsAutomationAgent,
    "eval_quality": EvalQualityAgent,
    "ops_observability": OpsObservabilityAgent,
}


class Orchestrator:
    def __init__(self, context: RunContext):
        self.context = context
        self.metrics: Dict[str, Any] = {"stages": {}}
        self.artifacts: Dict[str, Any] = {}
        self.context_data: Dict[str, Any] = {
            "title": context.task.title,
            "description": context.task.description,
            "repo_root": str(context.repo_root),
            "safe_mode": context.safe_mode,
        }

    def _write_checkpoint(self, stage: str, payload: Dict[str, Any]) -> None:
        write_json(self.context.run_dir / "checkpoint.json", {"stage": stage, "payload": payload})

    def _run_stage(self, name: str, agent_names: List[str]) -> Dict[str, Any]:
        stage_start = clock_ms()
        results = {}
        for agent_name in agent_names:
            agent = AGENT_REGISTRY[agent_name]()
            result = agent.run(self.context_data)
            results[agent_name] = result.payload
            self.context_data[f"{agent_name}_result"] = result.payload
        stage_end = clock_ms()
        self.metrics["stages"][name] = {
            "duration_ms": human_duration_ms(stage_start, stage_end),
            "agents": agent_names,
        }
        self._write_checkpoint(name, results)
        return results

    def run(self) -> Dict[str, Any]:
        start = clock_ms()
        repo_hash = hash_files(repo_files(self.context.repo_root))
        cache_dir = Path(".warforge") / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = cache_dir / "repo_index.json"
        cache_hit = cache_path.exists() and cache_path.read_text().strip().endswith(repo_hash)
        cache_payload = {"repo_hash": repo_hash, "cached_at": now_iso()}
        cache_path.write_text(f"{json.dumps(cache_payload)}\n{repo_hash}")
        self.metrics["cache_hit"] = cache_hit
        self.metrics["retries_count"] = 0

        plan_results = self._run_stage("plan", ["router", "repo_analyst", "planner", "orchestration_architect"])
        repo_scripts = detect_verification_commands(self.context.repo_root)
        self.context_data["verification_commands"] = [" ".join(command) for command in repo_scripts]
        implement_results = self._run_stage("implementation", ["implementer", "ai_integrations", "bots_automation"])
        verify_results = self._run_stage("verification", ["test_engineer", "eval_quality", "ops_observability"])
        review_results = self._run_stage("review", ["reviewer"])
        end = clock_ms()

        self.metrics["total_duration_ms"] = human_duration_ms(start, end)
        self.metrics["mode"] = "fast" if self.context.fast_mode else "safe"
        self.metrics["generated_at"] = now_iso()

        diff_text = "".join(json.dumps(self.context_data, sort_keys=True))
        repo_paths = [Path(path) for path in plan_results.get("repo_analyst", {}).get("repo_files", [])]
        policy = evaluate_policy(repo_paths, diff_text, self.context.safe_mode)

        result = {
            "plan": plan_results,
            "implementation": implement_results,
            "verification": verify_results,
            "review": review_results,
            "policy": {
                "restricted_zones": policy.restricted_zones,
                "requires_approval": policy.requires_approval,
            },
            "metrics": self.metrics,
        }
        return result

    def write_artifacts(self, payload: Dict[str, Any]) -> None:
        run_dir = self.context.run_dir
        write_json(run_dir / "plan.json", payload["plan"])
        write_json(run_dir / "repo_map.json", payload["plan"]["repo_analyst"]["repo_map"])
        write_json(run_dir / "workflow.json", payload["plan"]["orchestration_architect"])
        write_json(run_dir / "risk_report.json", payload["policy"])
        write_json(run_dir / "eval_report.json", payload["verification"]["eval_quality"])
        write_json(run_dir / "review_report.json", payload["review"]["reviewer"])
        write_json(run_dir / "metrics.json", payload["metrics"])
