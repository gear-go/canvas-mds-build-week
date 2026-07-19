from __future__ import annotations

from pathlib import Path
from typing import Any

from planning_alignment import validate_planning_alignment

ALLOWED_EVIDENCE_SCOPES = {"individual", "team", "mixed"}
SELF_OR_PEER_DIMENSIONS = {"self_assessment", "peer_assessment"}
LOW_COGNITIVE_QUESTION_TYPES = {"multiple_choice", "true_false", "matching"}
ACCEPTED_DECISION_STATUSES = {"confirmed", "modified"}
CLOSED_DECISION_STATUSES = ACCEPTED_DECISION_STATUSES | {"rejected"}
REQUIRED_ADVERSARIAL_CATEGORIES = {
    "ai_without_understanding",
    "unequal_team_contribution",
}


def _nonempty(value: Any) -> bool:
    return bool(str(value or "").strip())


def _items(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError(f"{label} debe ser una lista de objetos.")
    return value


def _unique_ids(items: list[dict[str, Any]], label: str) -> set[str]:
    ids = [str(item.get("id") or "").strip() for item in items]
    if any(not item for item in ids):
        raise ValueError(f"Cada elemento de {label} requiere un id.")
    if len(ids) != len(set(ids)):
        raise ValueError(f"{label} contiene ids duplicados.")
    return set(ids)


def _require_refs(values: Any, allowed: set[str], label: str) -> None:
    if not isinstance(values, list) or not values:
        raise ValueError(f"{label} requiere al menos una referencia.")
    refs = {str(item) for item in values}
    unknown = refs - allowed
    if unknown:
        raise ValueError(f"{label} contiene referencias desconocidas: {sorted(unknown)}")


def validate_redesign_artifact(artifact: dict[str, Any]) -> None:
    if not _nonempty(artifact.get("schema_version")):
        raise ValueError("El rediseño pedagógico requiere schema_version.")
    if not _nonempty(artifact.get("redesign_id")):
        raise ValueError("El rediseño pedagógico requiere redesign_id.")
    if artifact.get("unresolved_decisions"):
        raise ValueError("El rediseño todavía contiene decisiones no resueltas.")

    sources = _items(artifact.get("source_evidence"), "source_evidence")
    if not sources:
        raise ValueError("El rediseño requiere evidencia fuente.")
    source_ids = _unique_ids(sources, "source_evidence")
    for source in sources:
        path = str(source.get("path") or "").strip()
        if not path or Path(path).is_absolute() or "://" in path:
            raise ValueError("Las fuentes deben usar rutas relativas y portables.")
        if source.get("authority") not in {
            "documented",
            "faculty_confirmed",
            "model_proposal",
        }:
            raise ValueError("Cada fuente requiere una autoridad válida.")

    diagnosis = artifact.get("diagnosis")
    if not isinstance(diagnosis, dict):
        raise ValueError("El rediseño requiere diagnosis.")
    if not _nonempty(diagnosis.get("assessment_validity_problem")):
        raise ValueError("El diagnóstico requiere un problema de validez.")
    if not diagnosis.get("invisible_learning_processes"):
        raise ValueError("El diagnóstico debe identificar procesos de aprendizaje invisibles.")
    if not diagnosis.get("ai_validity_risks"):
        raise ValueError("El diagnóstico debe identificar riesgos de validez asociados a IA.")
    _require_refs(diagnosis.get("evidence_refs"), source_ids, "diagnosis.evidence_refs")

    questions = _items(artifact.get("faculty_questions"), "faculty_questions")
    if not 1 <= len(questions) <= 3:
        raise ValueError("El rediseño requiere entre una y tres preguntas docentes.")
    question_ids = _unique_ids(questions, "faculty_questions")
    for question in questions:
        if question.get("status") != "answered" or not _nonempty(question.get("answer")):
            raise ValueError("Todas las preguntas docentes deben estar respondidas.")
        _require_refs(question.get("evidence_refs"), source_ids, "faculty_questions.evidence_refs")

    decisions = _items(artifact.get("faculty_decisions"), "faculty_decisions")
    if not decisions:
        raise ValueError("El rediseño requiere decisiones docentes.")
    decision_ids = _unique_ids(decisions, "faculty_decisions")
    accepted_ids: set[str] = set()
    for decision in decisions:
        status = decision.get("status")
        if status not in CLOSED_DECISION_STATUSES:
            raise ValueError("Cada decisión docente debe estar confirmada, modificada o rechazada.")
        if status in ACCEPTED_DECISION_STATUSES:
            accepted_ids.add(str(decision["id"]))
        question_refs = decision.get("source_question_ids") or []
        unknown = {str(item) for item in question_refs} - question_ids
        if unknown:
            raise ValueError(f"Una decisión referencia preguntas desconocidas: {sorted(unknown)}")
        if not _nonempty(decision.get("decision")) or not _nonempty(decision.get("rationale")):
            raise ValueError("Cada decisión docente requiere decisión y fundamento.")
    if not accepted_ids:
        raise ValueError("El rediseño requiere al menos una decisión aceptada.")

    alignment = artifact.get("planning_alignment")
    if str(artifact.get("schema_version") or "").startswith("0.3") and not isinstance(
        alignment, dict
    ):
        raise ValueError("El rediseño 0.3 requiere planning_alignment.")
    if isinstance(alignment, dict):
        validate_planning_alignment(
            alignment,
            source_ids=source_ids,
            accepted_decision_ids=accepted_ids,
        )

    options = _items(artifact.get("redesign_options"), "redesign_options")
    if len(options) < 2:
        raise ValueError("El rediseño requiere al menos dos alternativas.")
    option_ids = _unique_ids(options, "redesign_options")
    selected = [item for item in options if item.get("selected") is True]
    if len(selected) != 1:
        raise ValueError("Debe existir exactamente una alternativa seleccionada.")
    for option in options:
        if not option.get("tradeoffs") or not _nonempty(option.get("faculty_workload")):
            raise ValueError("Cada alternativa requiere trade-offs y carga docente.")

    selected_design = artifact.get("selected_design")
    if not isinstance(selected_design, dict):
        raise ValueError("El rediseño requiere selected_design.")
    selected_option_id = str(selected_design.get("option_id") or "")
    if selected_option_id != str(selected[0].get("id")) or selected_option_id not in option_ids:
        raise ValueError("selected_design no coincide con la alternativa seleccionada.")
    if not selected_design.get("process_checkpoints"):
        raise ValueError("El diseño seleccionado requiere checkpoints del proceso.")
    if not selected_design.get("individual_evidence"):
        raise ValueError("El diseño seleccionado requiere evidencia individual.")
    if not selected_design.get("feedback_loops"):
        raise ValueError("El diseño seleccionado requiere un ciclo de feedback.")
    if not selected_design.get("ai_use_evidence"):
        raise ValueError("El diseño seleccionado requiere evidencia del uso de IA.")

    scenarios = _items(artifact.get("adversarial_scenarios"), "adversarial_scenarios")
    if len(scenarios) < 2:
        raise ValueError("El rediseño requiere al menos dos escenarios adversariales.")
    _unique_ids(scenarios, "adversarial_scenarios")
    categories = {str(item.get("category") or "") for item in scenarios}
    missing_categories = REQUIRED_ADVERSARIAL_CATEGORIES - categories
    if missing_categories:
        raise ValueError(
            f"Faltan escenarios adversariales requeridos: {sorted(missing_categories)}"
        )
    for scenario in scenarios:
        if not all(
            _nonempty(scenario.get(field))
            for field in ("scenario", "risk", "mitigation")
        ):
            raise ValueError("Cada escenario requiere escenario, riesgo y mitigación.")

    # Keep IDs available to callers through deterministic re-validation.
    if len(decision_ids) != len(decisions):
        raise ValueError("Las decisiones docentes no son trazables.")


def process_metrics(blueprint: dict[str, Any]) -> dict[str, Any]:
    assignments = blueprint.get("assignments") or []
    learning_outcomes = set((blueprint.get("learning_outcomes") or {}).keys())
    covered_outcomes = {
        str(outcome)
        for assignment in assignments
        for outcome in assignment.get("ra") or []
    }
    final_outcomes = {
        str(outcome)
        for assignment in assignments
        if assignment.get("process_stage") == "final_product"
        for outcome in assignment.get("ra") or []
    }
    nonfinal_outcomes = {
        str(outcome)
        for assignment in assignments
        if assignment.get("process_stage") != "final_product"
        for outcome in assignment.get("ra") or []
    }

    def weight(item: dict[str, Any]) -> float:
        return float(item.get("course_weight_percent") or 0)

    return {
        "product_weight_percent": round(
            sum(weight(item) for item in assignments if item.get("process_stage") == "final_product"),
            6,
        ),
        "process_weight_percent": round(
            sum(weight(item) for item in assignments if item.get("process_stage") != "final_product"),
            6,
        ),
        "individual_evidence_weight_percent": round(
            sum(weight(item) for item in assignments if item.get("evidence_scope") == "individual"),
            6,
        ),
        "process_evidence_count": sum(
            1 for item in assignments if item.get("process_stage") != "final_product"
        ),
        "all_learning_outcomes_covered": learning_outcomes <= covered_outcomes,
        "final_product_outcomes_have_process_evidence": final_outcomes <= nonfinal_outcomes,
        "has_individual_evidence": any(
            item.get("evidence_scope") == "individual" for item in assignments
        ),
        "has_feedback_iteration": any(
            (item.get("feedback_loop") or {}).get("requires_response") is True
            for item in assignments
        ),
        "has_ai_use_disclosure": any(
            (item.get("ai_use") or {}).get("disclosure_required") is True
            for item in assignments
        ),
    }


def validate_process_blueprint(blueprint: dict[str, Any]) -> dict[str, Any]:
    policy = blueprint.get("process_assessment_policy") or {}
    if policy.get("enabled") is not True:
        return {}

    artifact = blueprint.get("pedagogical_redesign")
    if not isinstance(artifact, dict):
        raise ValueError("La política de proceso requiere pedagogical_redesign.")
    validate_redesign_artifact(artifact)

    sources = artifact.get("source_evidence") or []
    source_ids = {str(item["id"]) for item in sources}
    decisions = artifact.get("faculty_decisions") or []
    accepted_decision_ids = {
        str(item["id"])
        for item in decisions
        if item.get("status") in ACCEPTED_DECISION_STATUSES
    }
    knowledge_base_refs = {
        str(item) for item in policy.get("knowledge_base_refs") or []
    }
    if knowledge_base_refs:
        source_roles = {str(item.get("role") or "") for item in sources}
        if "udd_active_learning_knowledge_base" not in source_roles:
            raise ValueError("La política UDD requiere su base de conocimiento como fuente.")
        _require_refs(
            (artifact.get("selected_design") or {}).get("knowledge_base_refs"),
            knowledge_base_refs,
            "selected_design.knowledge_base_refs",
        )

    assignments = blueprint.get("assignments") or []
    if not assignments:
        raise ValueError("La política de proceso requiere actividades.")
    assignment_keys = {str(item.get("key") or "") for item in assignments}
    learning_outcomes = set((blueprint.get("learning_outcomes") or {}).keys())
    total_weight = 0.0
    for assignment in assignments:
        key = str(assignment.get("key") or "")
        if assignment.get("course_weight_percent") is None:
            raise ValueError(f"La actividad {key} requiere course_weight_percent.")
        total_weight += float(assignment.get("course_weight_percent") or 0)
        if not _nonempty(assignment.get("process_stage")):
            raise ValueError(f"La actividad {key} requiere process_stage.")
        if assignment.get("evidence_scope") not in ALLOWED_EVIDENCE_SCOPES:
            raise ValueError(f"La actividad {key} requiere evidence_scope válido.")
        if not assignment.get("process_dimensions"):
            raise ValueError(f"La actividad {key} requiere process_dimensions.")
        unknown_outcomes = {str(item) for item in assignment.get("ra") or []} - learning_outcomes
        if unknown_outcomes:
            raise ValueError(
                f"La actividad {key} referencia resultados de aprendizaje desconocidos: "
                f"{sorted(unknown_outcomes)}"
            )
        if not assignment.get("cognitive_processes"):
            raise ValueError(f"La actividad {key} requiere cognitive_processes.")
        if not assignment.get("knowledge_dimensions"):
            raise ValueError(f"La actividad {key} requiere knowledge_dimensions.")
        if not assignment.get("alternative_evidence_formats"):
            raise ValueError(f"La actividad {key} requiere alternative_evidence_formats.")
        ai_use = assignment.get("ai_use")
        if not isinstance(ai_use, dict) or not _nonempty(ai_use.get("level")):
            raise ValueError(f"La actividad {key} requiere ai_use.level.")
        for field in ("disclosure_required", "verification_required"):
            if not isinstance(ai_use.get(field), bool):
                raise ValueError(f"La actividad {key} requiere ai_use.{field} booleano.")
        feedback = assignment.get("feedback_loop")
        if not isinstance(feedback, dict):
            raise ValueError(f"La actividad {key} requiere feedback_loop.")
        for field in ("receives_feedback", "requires_response"):
            if not isinstance(feedback.get(field), bool):
                raise ValueError(f"La actividad {key} requiere feedback_loop.{field} booleano.")
        if feedback.get("receives_feedback") is True and not _nonempty(feedback.get("actor")):
            raise ValueError(f"La actividad {key} debe identificar el actor del feedback.")
        if feedback.get("requires_response") is True:
            response_key = str(feedback.get("response_in_assignment_key") or "")
            if response_key not in assignment_keys:
                raise ValueError(
                    f"La actividad {key} debe vincular su respuesta a una actividad existente."
                )
        if knowledge_base_refs:
            _require_refs(
                assignment.get("knowledge_base_refs"),
                knowledge_base_refs,
                f"{key}.knowledge_base_refs",
            )
        _require_refs(
            assignment.get("source_evidence_ids"),
            source_ids,
            f"{key}.source_evidence_ids",
        )
        _require_refs(
            assignment.get("faculty_decision_ids"),
            accepted_decision_ids,
            f"{key}.faculty_decision_ids",
        )

    if round(total_weight, 6) != 100:
        raise ValueError("Las actividades del diseño de proceso no suman 100% del curso.")

    if policy.get("require_self_or_peer_assessment") is True:
        dimensions = {
            str(dimension)
            for assignment in assignments
            for dimension in assignment.get("process_dimensions") or []
        }
        if not dimensions.intersection(SELF_OR_PEER_DIMENSIONS):
            raise ValueError("La política UDD requiere autoevaluación o coevaluación.")

    if policy.get("require_alternative_evidence_formats") is True:
        missing_formats = [
            str(item.get("key") or "")
            for item in assignments
            if not item.get("alternative_evidence_formats")
        ]
        if missing_formats:
            raise ValueError(
                "Faltan formatos alternativos de evidencia en: "
                f"{sorted(missing_formats)}"
            )

    quizzes = [
        item for item in assignments if isinstance(item.get("quiz_settings"), dict)
    ]
    for quiz in quizzes:
        question_types = {
            str(question.get("type") or "")
            for question in (quiz.get("quiz_settings") or {}).get("questions") or []
        }
        if question_types and question_types <= LOW_COGNITIVE_QUESTION_TYPES:
            raise ValueError(
                f"El quiz {quiz.get('key')} solo observa demanda cognitiva baja."
            )

    checkpoints = (artifact.get("selected_design") or {}).get("process_checkpoints") or []
    checkpoint_keys = {
        str(item.get("assignment_key") or "")
        for item in checkpoints
        if isinstance(item, dict)
    }
    unknown_checkpoints = checkpoint_keys - assignment_keys
    if unknown_checkpoints:
        raise ValueError(
            f"El diseño seleccionado referencia actividades desconocidas: {sorted(unknown_checkpoints)}"
        )

    metrics = process_metrics(blueprint)
    minimum = float(policy.get("minimum_process_weight_percent") or 0)
    if metrics["process_weight_percent"] < minimum:
        raise ValueError(
            "El peso de evidencia del proceso es inferior al mínimo aprobado."
        )
    if not metrics["all_learning_outcomes_covered"]:
        raise ValueError("No todos los resultados de aprendizaje tienen evidencia.")
    if not metrics["final_product_outcomes_have_process_evidence"]:
        raise ValueError(
            "Algún resultado observado en el producto final no tiene evidencia del proceso."
        )
    has_team_evidence = any(
        item.get("evidence_scope") in {"team", "mixed"} for item in assignments
    )
    if (
        policy.get("require_individual_evidence_for_group_work") is True
        and has_team_evidence
        and not metrics["has_individual_evidence"]
    ):
        raise ValueError("El trabajo grupal requiere evidencia individual.")
    if (
        policy.get("require_feedback_iteration") is True
        and not metrics["has_feedback_iteration"]
    ):
        raise ValueError("La política requiere una iteración basada en feedback.")
    if (
        policy.get("require_ai_use_disclosure") is True
        and not metrics["has_ai_use_disclosure"]
    ):
        raise ValueError("La política requiere evidencia declarada del uso de IA.")
    return metrics


def render_before_after(blueprint: dict[str, Any]) -> str:
    artifact = blueprint["pedagogical_redesign"]
    validate_process_blueprint(blueprint)
    current = artifact["current_assessment"]
    metrics = process_metrics(blueprint)
    diagnosis = artifact["diagnosis"]
    selected = next(
        item for item in artifact["redesign_options"] if item.get("selected") is True
    )

    lines = [
        f"# Process-Centered Assessment Redesign · {blueprint.get('course_profile')}",
        "",
        "> This report contains concise, evidence-linked design rationales, not hidden model reasoning.",
        "",
        "## Why the current assessment needs redesign",
        "",
        str(diagnosis["assessment_validity_problem"]),
        "",
        "### Learning processes that were previously invisible",
        "",
    ]
    lines.extend(
        f"- {item}" for item in diagnosis.get("invisible_learning_processes") or []
    )
    lines.extend(
        [
            "",
            "## Before and after",
            "",
            "| Evidence model | Before | Approved redesign |",
            "|---|---:|---:|",
            f"| Final product | {current.get('product_weight_percent', 0)}% | {metrics['product_weight_percent']}% |",
            f"| Process evidence | {current.get('process_weight_percent', 0)}% | {metrics['process_weight_percent']}% |",
            f"| Individual evidence | {current.get('individual_evidence_weight_percent', 0)}% | {metrics['individual_evidence_weight_percent']}% |",
            "",
            f"Selected option: **{selected.get('name')}**",
            "",
            f"Faculty workload: {selected.get('faculty_workload')}",
            "",
            "Trade-offs:",
        ]
    )
    lines.extend(f"- {item}" for item in selected.get("tradeoffs") or [])
    lines.extend(["", "## Confirmed faculty decisions", ""])
    for decision in artifact.get("faculty_decisions") or []:
        if decision.get("status") in ACCEPTED_DECISION_STATUSES:
            lines.append(
                f"- **{decision.get('id')}**: {decision.get('decision')} — {decision.get('rationale')}"
            )
    lines.extend(["", "## Process evidence map", ""])
    lines.append("| Activity | Stage | Scope | Weight | Visible process |")
    lines.append("|---|---|---|---:|---|")
    for assignment in blueprint.get("assignments") or []:
        dimensions = ", ".join(assignment.get("process_dimensions") or [])
        lines.append(
            f"| {assignment.get('name')} | {assignment.get('process_stage')} | "
            f"{assignment.get('evidence_scope')} | {assignment.get('course_weight_percent')}% | "
            f"{dimensions} |"
        )
    lines.extend(["", "## Adversarial validity checks", ""])
    for scenario in artifact.get("adversarial_scenarios") or []:
        lines.extend(
            [
                f"### {scenario.get('id')} · {scenario.get('scenario')}",
                "",
                f"- Risk: {scenario.get('risk')}",
                f"- Mitigation: {scenario.get('mitigation')}",
                "",
            ]
        )
    lines.extend(
        [
            "## Safety boundary",
            "",
            "- GPT-5.6 proposed the diagnosis and alternatives from course evidence.",
            "- The instructor confirmed the material pedagogical decisions.",
            "- The deterministic engine validated weights, traceability, process evidence, and safety gates.",
            "- No student data was used and no Canvas object was published.",
            "",
        ]
    )
    return "\n".join(lines)
