from pathlib import Path

from warforge.policy import detect_restricted_zones, evaluate_policy


def test_detect_restricted_zones_from_path():
    paths = [Path("auth/login.py"), Path("src/app.py")]
    zones = detect_restricted_zones(paths, "")
    assert "auth" in zones


def test_evaluate_policy_requires_approval_in_safe_mode():
    result = evaluate_policy([Path("infra/terraform/main.tf")], "", safe_mode=True)
    assert result.requires_approval is True
