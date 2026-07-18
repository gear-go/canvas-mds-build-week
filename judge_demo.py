#!/usr/bin/env python3
"""Run a credential-free, offline judge experience for Canvas MDS."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent
ENGINE_DIR = REPO_ROOT / "plugins" / "canvas-mds" / "scripts"
DEFAULT_PROFILE = (
    REPO_ROOT
    / "plugins"
    / "canvas-mds"
    / "assets"
    / "profiles"
    / "entornos-digitales-2026.json"
)

if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from canvas_mds import CanvasMVPError, build_dry_run  # noqa: E402
from canvas_mds_apply import validate_blueprint  # noqa: E402


def load_profile(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise CanvasMVPError(f"Could not read the course profile: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CanvasMVPError(f"The course profile is not valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise CanvasMVPError("The course profile must be a JSON object.")
    return payload


def synthetic_empty_snapshot(blueprint: dict[str, Any]) -> dict[str, Any]:
    required_terms = (blueprint.get("course_identity") or {}).get("required_terms") or []
    identity = str(required_terms[0] if required_terms else "Canvas MDS")
    return {
        "metadata": {
            "source": "synthetic_offline_judge_demo",
            "permission_issues": [],
        },
        "course": {
            "id": "offline-judge-demo",
            "name": f"Judge Sandbox · {identity}",
            "workflow_state": "unpublished",
            "apply_assignment_group_weights": True,
        },
        "modules": [],
        "pages": [],
        "assignments": [],
        "assignment_groups": [],
        "rubrics": [],
        "tabs": [],
    }


def all_planned_objects_are_unpublished(plan: dict[str, Any]) -> bool:
    assignments_ok = all(item.get("published") is False for item in plan["assignments"])
    modules_ok = all(item.get("published") is False for item in plan["modules"])
    pages_ok = all(
        page.get("published") is False
        for module in plan["modules"]
        for page in module["pages_plan"]
    )
    return assignments_ok and modules_ok and pages_ok


def empty_snapshot_requires_all_proposed_objects(plan: dict[str, Any]) -> bool:
    proposed = plan["proposed"]
    actions = plan["actions"]
    return (
        actions["modules_to_create"] == proposed["modules"]
        and actions["pages_to_create"] == proposed["unique_pages"]
        and actions["assignments_to_create"] == proposed["assignments"]
        and actions["groups_to_create"] == proposed["assignment_groups"]
    )


def run_demo(profile_path: Path) -> dict[str, Any]:
    blueprint = load_profile(profile_path)
    validate_blueprint(blueprint)

    snapshot = synthetic_empty_snapshot(blueprint)
    plan = build_dry_run(snapshot, blueprint)
    quizzes = [
        item
        for item in blueprint.get("assignments") or []
        if isinstance(item.get("quiz_settings"), dict)
    ]

    checks = {
        "profile_valid": True,
        "default_publish_is_false": blueprint.get("default_publish") is False,
        "no_pending_manual_decisions": not blueprint.get("manual_decisions"),
        "assignment_groups_sum_to_100": sum(
            float(item.get("weight") or 0)
            for item in blueprint.get("assignment_groups") or []
        )
        == 100,
        "exactly_one_classic_quiz": len(quizzes) == 1,
        "canvas_mutations_are_zero": plan["metadata"]["canvas_mutations"] == 0,
        "all_planned_objects_are_unpublished": all_planned_objects_are_unpublished(plan),
        "empty_snapshot_requires_all_proposed_objects": (
            empty_snapshot_requires_all_proposed_objects(plan)
        ),
        "no_network_or_canvas_access_used": True,
        "no_credentials_required": True,
    }
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise CanvasMVPError(f"Offline judge checks failed: {', '.join(failed)}")

    return {
        "status": "PASS",
        "experience": "Canvas MDS offline judge demo",
        "profile": blueprint.get("course_profile"),
        "profile_path": str(profile_path),
        "sample_content_language": "Spanish (target deployment context)",
        "canvas_connection_used": False,
        "credentials_required": False,
        "canvas_mutations": plan["metadata"]["canvas_mutations"],
        "proposed": plan["proposed"],
        "actions": plan["actions"],
        "checks": checks,
        "note": (
            "The demo executed the production profile validator and dry-run planner "
            "against a synthetic empty Canvas snapshot. No HTTP request was attempted."
        ),
    }


def render_summary(result: dict[str, Any]) -> str:
    proposed = result["proposed"]
    checks = result["checks"]
    lines = [
        "Canvas MDS Offline Judge Demo",
        "=============================",
        f"Status: {result['status']}",
        f"Profile: {result['profile']}",
        "Canvas connection used: no",
        "Credentials required: no",
        f"Canvas mutations: {result['canvas_mutations']}",
        "",
        "Proposed course structure:",
        f"- Modules: {proposed['modules']}",
        f"- Unique pages: {proposed['unique_pages']}",
        f"- Assignments: {proposed['assignments']}",
        f"- Assignment groups: {proposed['assignment_groups']}",
        "",
        "Safety and validity checks:",
    ]
    lines.extend(
        f"- {'PASS' if passed else 'FAIL'}: {name.replace('_', ' ')}"
        for name, passed in checks.items()
    )
    lines.extend(["", result["note"]])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the sample Canvas MDS profile and run the production dry-run "
            "planner without credentials, network access, or Canvas mutations."
        )
    )
    parser.add_argument(
        "--profile",
        type=Path,
        default=DEFAULT_PROFILE,
        help="Path to a Canvas MDS course profile JSON file.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the result as JSON instead of the human-readable summary.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = run_demo(args.profile.resolve())
    except CanvasMVPError as exc:
        print(f"Judge demo failed: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_summary(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
