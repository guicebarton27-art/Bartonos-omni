from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


RESTRICTED_PATTERNS = {
    "auth": re.compile(r"auth|login|oauth|jwt", re.IGNORECASE),
    "payments": re.compile(r"payment|billing|stripe|paypal", re.IGNORECASE),
    "secrets": re.compile(r"secret|token|key", re.IGNORECASE),
    "infra": re.compile(r"terraform|k8s|docker|ci", re.IGNORECASE),
    "migrations": re.compile(r"migration|migrate|schema", re.IGNORECASE),
}

RESTRICTED_PATHS = {
    "auth": ["auth", "security"],
    "payments": ["payments", "billing"],
    "secrets": ["secrets", "vault"],
    "infra": ["infra", "terraform", ".github", "ci"],
    "migrations": ["migrations", "schema"],
}


@dataclass
class PolicyResult:
    restricted_zones: List[str]
    requires_approval: bool
    safe_mode: bool


def detect_restricted_zones(paths: Iterable[Path], diff_text: str) -> List[str]:
    zones: List[str] = []
    for zone, patterns in RESTRICTED_PATHS.items():
        if any(part in str(path).lower() for path in paths for part in patterns):
            zones.append(zone)
    for zone, pattern in RESTRICTED_PATTERNS.items():
        if pattern.search(diff_text):
            zones.append(zone)
    return sorted(set(zones))


def evaluate_policy(paths: Iterable[Path], diff_text: str, safe_mode: bool) -> PolicyResult:
    restricted = detect_restricted_zones(paths, diff_text)
    requires_approval = bool(restricted) and safe_mode
    return PolicyResult(restricted_zones=restricted, requires_approval=requires_approval, safe_mode=safe_mode)
