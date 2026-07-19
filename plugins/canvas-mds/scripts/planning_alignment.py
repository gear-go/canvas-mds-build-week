from __future__ import annotations

import unicodedata
from typing import Any

AMBIGUOUS_ACTIONS = {"aprender", "conocer", "entender", "comprender", "familiarizarse"}
OBJECTIVE_COMPONENTS = {"action", "content_or_performance", "condition"}


def _text(value: Any) -> bool:
    return bool(str(value or "").strip())

# alignment helpers


def _items(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError(f"{label} debe ser una lista de objetos.")
    return value


def _ids(items: list[dict[str, Any]], label: str) -> set[str]:
    values = [str(item.get("id") or "").strip() for item in items]
    if any(not value for value in values) or len(values) != len(set(values)):
        raise ValueError(f"{label} requiere ids unicos y no vacios.")
    return set(values)


def _refs(values: Any, allowed: set[str], label: str) -> set[str]:
    if not isinstance(values, list) or not values:
        raise ValueError(f"{label} requiere referencias.")
    refs = {str(value) for value in values}
    unknown = refs - allowed
    if unknown:
        raise ValueError(f"{label} contiene referencias desconocidas: {sorted(unknown)}")
    return refs


def _normal(value: Any) -> str:
    value = unicodedata.normalize("NFKD", str(value or "").lower().strip())
    return "".join(char for char in value if not unicodedata.combining(char))


def validate_planning_alignment(
    alignment: dict[str, Any],
    *,
    source_ids: set[str] | None = None,
    accepted_decision_ids: set[str] | None = None,
) -> dict[str, Any]:
    if not isinstance(alignment, dict):
        raise ValueError("planning_alignment debe ser un objeto.")
    for field in ("schema_version", "alignment_id", "need", "audience"):
        if not _text(alignment.get(field)):
            raise ValueError(f"planning_alignment requiere {field}.")
    if alignment.get("alignment_status") != "confirmed":
        raise ValueError("ALIGNMENT STOP: el alineamiento debe estar confirmado.")
    if alignment.get("unresolved_decisions"):
        raise ValueError("ALIGNMENT STOP: quedan decisiones no resueltas.")
    if alignment.get("scope") not in {"course", "unit", "workshop", "assessment", "intervention"}:
        raise ValueError("planning_alignment requiere un scope valido.")
    duration = alignment.get("duration")
    if not isinstance(duration, dict) or duration.get("unit") not in {
        "minutes", "hours", "days", "weeks"
    }:
        raise ValueError("planning_alignment requiere duration valida.")
    try:
        if float(duration.get("value")) <= 0:
            raise ValueError
    except (TypeError, ValueError):
        raise ValueError("duration.value debe ser positivo.") from None

    objectives = _items(alignment.get("objectives"), "objectives")
    if not objectives:
        raise ValueError("Se requiere al menos un objetivo.")
    objective_ids = _ids(objectives, "objectives")
    for objective in objectives:
        oid = str(objective["id"])
        for field in ("statement", "observable_action", "content_or_performance", "condition"):
            if not _text(objective.get(field)):
                raise ValueError(f"El objetivo {oid} requiere {field}.")
        if objective.get("activity_free") is not True:
            raise ValueError(f"El objetivo {oid} confunde resultado y actividad.")
        if _normal(objective.get("observable_action")) in AMBIGUOUS_ACTIONS:
            raise ValueError(f"El objetivo {oid} usa una accion no observable.")
        if objective.get("status") not in {"documented", "faculty_confirmed"}:
            raise ValueError(f"El objetivo {oid} requiere autoridad valida.")
        if source_ids is not None:
            _refs(objective.get("source_evidence_ids"), source_ids, f"{oid}.source_evidence_ids")
        if objective.get("status") == "faculty_confirmed":
            allowed = accepted_decision_ids
            if allowed is None:
                if not objective.get("faculty_decision_ids"):
                    raise ValueError(f"El objetivo {oid} requiere decision docente.")
            else:
                _refs(objective.get("faculty_decision_ids"), allowed, f"{oid}.faculty_decision_ids")

    indicators = _items(alignment.get("indicators"), "indicators")
    if not 4 <= len(indicators) <= 6:
        raise ValueError("Se requieren entre cuatro y seis indicadores.")
    indicator_ids = _ids(indicators, "indicators")
    evidence = _items(alignment.get("evidence"), "evidence")
    if not evidence:
        raise ValueError("Se requiere evidencia.")
    evidence_ids = _ids(evidence, "evidence")
    for indicator in indicators:
        iid = str(indicator["id"])
        if not _text(indicator.get("statement")) or indicator.get("observable") is not True:
            raise ValueError(f"El indicador {iid} debe ser observable.")
        if indicator.get("type") not in {"process", "result"}:
            raise ValueError(f"El indicador {iid} requiere tipo process o result.")
        if indicator.get("attendance_or_participation_only") is not False:
            raise ValueError(f"El indicador {iid} no puede medir solo asistencia o participacion.")
        statement = _normal(indicator.get("statement"))
        if any(term in statement for term in ("correctamente", "adecuadamente", "de buena manera")):
            if not _text(indicator.get("quality_condition")):
                raise ValueError(f"El indicador {iid} debe definir su condicion de calidad.")
        _refs(indicator.get("objective_ids"), objective_ids, f"{iid}.objective_ids")
        linked_evidence = _refs(
            indicator.get("evidence_ids"), evidence_ids, f"{iid}.evidence_ids"
        )
        for eid in linked_evidence:
            evidence_item = next(value for value in evidence if str(value["id"]) == eid)
            if iid not in {str(value) for value in evidence_item.get("indicator_ids") or []}:
                raise ValueError("La relacion indicador-evidencia debe ser bidireccional.")

    for item in evidence:
        eid = str(item["id"])
        if not _text(item.get("description")):
            raise ValueError(f"La evidencia {eid} requiere descripcion.")
        if item.get("scope") not in {"individual", "team", "mixed"}:
            raise ValueError(f"La evidencia {eid} requiere scope valido.")
        linked = _refs(item.get("indicator_ids"), indicator_ids, f"{eid}.indicator_ids")
        for iid in linked:
            indicator = next(value for value in indicators if str(value["id"]) == iid)
            if eid not in {str(value) for value in indicator.get("evidence_ids") or []}:
                raise ValueError("La relacion indicador-evidencia debe ser bidireccional.")

    instruments = _items(alignment.get("instruments"), "instruments")
    if len(instruments) < 3:
        raise ValueError("Se deben comparar al menos tres instrumentos.")
    instrument_ids = _ids(instruments, "instruments")
    selected = [item for item in instruments if item.get("selected") is True]
    primary = [item for item in selected if item.get("role") == "primary"]
    if len(primary) != 1:
        raise ValueError("Debe existir exactamente un instrumento principal.")
    total_workload = 0.0
    for instrument in instruments:
        iid = str(instrument["id"])
        if instrument.get("role") not in {"primary", "complementary", "considered"}:
            raise ValueError(f"El instrumento {iid} requiere role valido.")
        if not all(_text(instrument.get(field)) for field in (
            "type", "rationale", "advantages", "limitations"
        )):
            raise ValueError(f"El instrumento {iid} requiere comparacion completa.")
        if instrument.get("role") == "considered" and instrument.get("selected") is not False:
            raise ValueError(f"El instrumento considerado {iid} no puede quedar seleccionado.")
        if instrument.get("selected") is True:
            _refs(instrument.get("indicator_ids"), indicator_ids, f"{iid}.indicator_ids")
            _refs(instrument.get("evidence_ids"), evidence_ids, f"{iid}.evidence_ids")
            workload = instrument.get("review_workload")
            if not isinstance(workload, dict) or not _text(workload.get("reviewer")):
                raise ValueError(f"El instrumento {iid} requiere review_workload.")
            expected = float(workload.get("items_to_review")) * float(workload.get("minutes_per_item"))
            actual = float(workload.get("estimated_total_minutes"))
            if round(expected, 6) != round(actual, 6):
                raise ValueError(f"La carga de revision de {iid} no coincide.")
            total_workload += actual

    procedure = alignment.get("evaluation_procedure")
    if not isinstance(procedure, dict):
        raise ValueError("Se requiere evaluation_procedure.")
    moments = _items(procedure.get("moments"), "evaluation_procedure.moments")
    moment_ids = _ids(moments, "evaluation_procedure.moments")
    if "final" not in {str(item.get("stage")) for item in moments}:
        raise ValueError("El procedimiento requiere un momento final.")
    usable_feedback = False
    used_instruments: set[str] = set()
    for moment in moments:
        mid = str(moment["id"])
        if moment.get("stage") not in {"diagnostic", "follow_up", "final"}:
            raise ValueError(f"El momento {mid} requiere stage valido.")
        if not all(_text(moment.get(field)) for field in ("actor", "action", "feedback", "feedback_use")):
            raise ValueError(f"El momento {mid} requiere actor, accion y feedback utilizable.")
        _refs(moment.get("evidence_ids"), evidence_ids, f"{mid}.evidence_ids")
        used_instruments |= _refs(moment.get("instrument_ids"), instrument_ids, f"{mid}.instrument_ids")
        usable_feedback = usable_feedback or bool(moment.get("feedback_use"))
    if not usable_feedback:
        raise ValueError("El procedimiento no contiene feedback utilizable.")
    if {str(item["id"]) for item in selected} - used_instruments:
        raise ValueError("El procedimiento no usa todos los instrumentos seleccionados.")

    rows = _items(alignment.get("alignment_matrix"), "alignment_matrix")
    covered_components: set[str] = set()
    covered_objectives: set[str] = set()
    covered_indicators: set[str] = set()
    covered_evidence: set[str] = set()
    covered_instruments: set[str] = set()
    covered_moments: set[str] = set()
    for row in rows:
        component = str(row.get("objective_component") or "")
        if component not in OBJECTIVE_COMPONENTS:
            raise ValueError("La matriz requiere componentes validos del objetivo.")
        covered_components.add(component)
        covered_objectives |= _refs(row.get("objective_ids"), objective_ids, "matrix.objective_ids")
        covered_indicators |= _refs(row.get("indicator_ids"), indicator_ids, "matrix.indicator_ids")
        covered_evidence |= _refs(row.get("evidence_ids"), evidence_ids, "matrix.evidence_ids")
        covered_instruments |= _refs(
            row.get("instrument_ids"), {str(item["id"]) for item in selected}, "matrix.instrument_ids"
        )
        covered_moments |= _refs(row.get("procedure_moment_ids"), moment_ids, "matrix.procedure_moment_ids")
    if covered_components != OBJECTIVE_COMPONENTS or covered_objectives != objective_ids:
        raise ValueError("La matriz no cubre todos los objetivos y sus componentes.")
    if covered_indicators != indicator_ids or covered_evidence != evidence_ids:
        raise ValueError("La matriz no cubre todos los indicadores y evidencias.")
    if covered_instruments != {str(item["id"]) for item in selected} or covered_moments != moment_ids:
        raise ValueError("La matriz no cubre instrumentos y momentos seleccionados.")
    return {
        "objective_count": len(objectives),
        "indicator_count": len(indicators),
        "evidence_count": len(evidence),
        "selected_instrument_count": len(selected),
        "estimated_review_minutes": round(total_workload, 6),
    }
