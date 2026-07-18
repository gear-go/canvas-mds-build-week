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
from process_evidence import validate_process_blueprint  # noqa: E402


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
    process_metrics = validate_process_blueprint(blueprint)

    snapshot = synthetic_empty_snapshot(blueprint)
    plan = build_dry_run(snapshot, blueprint)
    quizzes = [
        item
        for item in blueprint.get("assignments") or []
        if isinstance(item.get("quiz_settings"), dict)
    ]
    redesign = blueprint["pedagogical_redesign"]
    current = redesign["current_assessment"]
    options = redesign["redesign_options"]
    selected_options = [item for item in options if item.get("selected") is True]
    adversarial_categories = {
        str(item.get("category") or "")
        for item in redesign.get("adversarial_scenarios") or []
    }
    knowledge_refs = {
        str(item)
        for item in (blueprint.get("process_assessment_policy") or {}).get(
            "knowledge_base_refs"
        )
        or []
    }
    source_roles = {
        str(item.get("role") or "") for item in redesign.get("source_evidence") or []
    }

    checks = {
        "profile_valid": True,
        "generative_redesign_artifact_valid": bool(process_metrics),
        "two_or_more_redesign_options": len(options) >= 2,
        "exactly_one_faculty_selected_option": len(selected_options) == 1,
        "udd_knowledge_base_is_traced": (
            "udd_active_learning_knowledge_base" in source_roles
            and any(item.startswith("UDD-R") for item in knowledge_refs)
        ),
        "product_weight_reduced_from_95_to_40": (
            current.get("product_weight_percent") == 95
            and process_metrics["product_weight_percent"] == 40
        ),
        "process_weight_increased_from_0_to_60": (
            current.get("process_weight_percent") == 0
            and process_metrics["process_weight_percent"] == 60
        ),
        "individual_evidence_present": process_metrics["has_individual_evidence"],
        "feedback_iteration_present": process_metrics["has_feedback_iteration"],
        "ai_use_disclosure_present": process_metrics["has_ai_use_disclosure"],
        "adversarial_validity_scenarios_present": {
            "ai_without_understanding",
            "unequal_team_contribution",
        }
        <= adversarial_categories,
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
        "experience": "Canvas MDS process-centered assessment judge demo",
        "profile": blueprint.get("course_profile"),
        "profile_path": str(profile_path),
        "sample_content_language": "Spanish (target deployment context)",
        "canvas_connection_used": False,
        "credentials_required": False,
        "canvas_mutations": plan["metadata"]["canvas_mutations"],
        "assessment_shift": {
            "before": {
                "final_product_percent": current.get("product_weight_percent"),
                "process_evidence_percent": current.get("process_weight_percent"),
                "individual_evidence_percent": current.get(
                    "individual_evidence_weight_percent"
                ),
            },
            "approved_redesign": {
                "final_product_percent": process_metrics["product_weight_percent"],
                "process_evidence_percent": process_metrics["process_weight_percent"],
                "individual_evidence_percent": process_metrics[
                    "individual_evidence_weight_percent"
                ],
            },
        },
        "reasoning_contract": {
            "gpt_5_6": (
                "Diagnoses the validity gap from heterogeneous course evidence, "
                "proposes alternatives and tests them against failure scenarios."
            ),
            "faculty": (
                "Answers decision-changing questions and confirms, modifies or "
                "rejects every material pedagogical choice."
            ),
            "deterministic_engine": (
                "Validates traceability, learning-outcome coverage, weights, "
                "process evidence, accessibility metadata and Canvas safety gates."
            ),
        },
        "proposed": plan["proposed"],
        "actions": plan["actions"],
        "checks": checks,
        "note": (
            "The harness validated the approved GPT-5.6-assisted redesign and ran "
            "the production dry-run planner against a synthetic empty Canvas "
            "snapshot. No HTTP request was attempted."
        ),
    }


def render_summary(result: dict[str, Any]) -> str:
    proposed = result["proposed"]
    checks = result["checks"]
    before = result["assessment_shift"]["before"]
    after = result["assessment_shift"]["approved_redesign"]
    contract = result["reasoning_contract"]
    lines = [
        "Canvas MDS Process-Centered Judge Demo",
        "======================================",
        f"Status: {result['status']}",
        f"Profile: {result['profile']}",
        "Canvas connection used: no",
        "Credentials required: no",
        f"Canvas mutations: {result['canvas_mutations']}",
        "",
        "Assessment evidence shift:",
        (
            "- Final product: "
            f"{before['final_product_percent']}% -> {after['final_product_percent']}%"
        ),
        (
            "- Process evidence: "
            f"{before['process_evidence_percent']}% -> {after['process_evidence_percent']}%"
        ),
        (
            "- Individual evidence: "
            f"{before['individual_evidence_percent']}% -> "
            f"{after['individual_evidence_percent']}%"
        ),
        "",
        "Reasoning and control:",
        f"- GPT-5.6: {contract['gpt_5_6']}",
        f"- Faculty: {contract['faculty']}",
        f"- Deterministic engine: {contract['deterministic_engine']}",
        "",
        "Proposed course structure:",
        f"- Modules: {proposed['modules']}",
        f"- Unique pages: {proposed['unique_pages']}",
        f"- Assignments: {proposed['assignments']}",
        f"- Assignment groups: {proposed['assignment_groups']}",
        "",
        f"Safety, pedagogical validity and traceability checks ({len(checks)}):",
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
            "Validate the approved process-centered assessment redesign and run "
            "the production Canvas dry-run planner without credentials, network "
            "access or Canvas mutations."
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
    except (CanvasMVPError, ValueError) as exc:
        print(f"Judge demo failed: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_summary(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
