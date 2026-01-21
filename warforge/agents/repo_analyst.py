from __future__ import annotations

from pathlib import Path

from warforge.agents.base import Agent, AgentResult
from warforge.core import build_repo_map, repo_files
from warforge.policy import detect_restricted_zones
from warforge.verification import detect_verification_commands


class RepoAnalystAgent(Agent):
    name = "repo_analyst"

    def run(self, context):
        repo_root = Path(context["repo_root"])
        files = [str(path.relative_to(repo_root)) for path in repo_files(repo_root)]
        scripts = [" ".join(command) for command in detect_verification_commands(repo_root)]
        repo_map = build_repo_map(repo_root)
        restricted = detect_restricted_zones([Path(file) for file in files], "")
        return AgentResult(
            name=self.name,
            payload={
                "stack": "python" if (repo_root / "pyproject.toml").exists() else "unknown",
                "scripts": scripts,
                "repo_files": files[:50],
                "repo_map": repo_map,
                "restricted_zones": restricted,
            },
        )
