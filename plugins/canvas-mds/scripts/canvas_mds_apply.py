from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import requests

from canvas_mds import (
    DEFAULT_BLUEPRINT,
    CanvasMVPError,
    CanvasReadOnlyClient,
    add_common_arguments,
    collect_snapshot,
    normalized,
    read_json_object,
    require_course_id,
    resolve_settings,
    resolve_token,
    write_json,
)


class CanvasWriteClient(CanvasReadOnlyClient):
    """Cliente de escritura limitado a POST y PUT, sin reintentos automáticos."""

    def __init__(self, base_url: str, token: str, timeout: int = 30) -> None:
        super().__init__(base_url, token, timeout=timeout)
        self.session.headers["User-Agent"] = "canvas-mds-portable-apply-unpublished/0.1"

    def mutate_json(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | list[tuple[str, Any]],
        action: str,
    ) -> dict[str, Any]:
        if method not in {"POST", "PUT"}:
            raise CanvasMVPError("El modo de aplicación solo admite POST y PUT.")
        url = self._absolute_url(endpoint)
        try:
            response = self.session.request(
                method,
                url,
                data=data,
                timeout=self.timeout,
                verify=True,
            )
        except requests.RequestException as exc:
            raise CanvasMVPError(
                f"Fallo de red durante {action}. No se reintentó para evitar duplicados; "
                "volver a ejecutar el comando idempotente."
            ) from exc
        if response.status_code in (401, 403):
            raise PermissionError(f"Canvas rechazó {action} (HTTP {response.status_code}).")
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            detail = ""
            try:
                error_payload = response.json()
                if isinstance(error_payload, dict):
                    safe_error = error_payload.get("errors") or error_payload.get("message")
                    if safe_error:
                        detail = " Detalle: " + json.dumps(
                            safe_error, ensure_ascii=False
                        )[:600]
            except (ValueError, TypeError):
                pass
            raise CanvasMVPError(
                f"Canvas rechazó {action} (HTTP {response.status_code}).{detail}"
            ) from exc
        payload = response.json()
        if not isinstance(payload, dict):
            raise CanvasMVPError(f"Canvas devolvió un formato inesperado durante {action}.")
        return payload

    def post_json(
        self,
        endpoint: str,
        data: dict[str, Any] | list[tuple[str, Any]],
        action: str,
    ) -> dict[str, Any]:
        return self.mutate_json("POST", endpoint, data, action)

    def put_json(
        self,
        endpoint: str,
        data: dict[str, Any] | list[tuple[str, Any]],
        action: str,
    ) -> dict[str, Any]:
        return self.mutate_json("PUT", endpoint, data, action)


def to_canvas_iso(value: str | None, timezone_name: str) -> str | None:
    if not value:
        return None
    local = datetime.strptime(value, "%Y-%m-%d %H:%M").replace(
        tzinfo=ZoneInfo(timezone_name)
    )
    return local.astimezone(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def unique_map(items: list[dict[str, Any]], field: str, label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        key = normalized(str(item.get(field) or "")).strip()
        if not key:
            continue
        if key in result:
            raise CanvasMVPError(f"Hay nombres duplicados en Canvas para {label}: {item.get(field)}")
        result[key] = item
    return result


def quiz_assignments(blueprint: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in blueprint.get("assignments") or []
        if isinstance(item.get("quiz_settings"), dict)
    ]


def validate_blueprint(blueprint: dict[str, Any]) -> None:
    if blueprint.get("default_publish") is not False:
        raise CanvasMVPError("El blueprint debe declarar default_publish=false.")
    if blueprint.get("manual_decisions"):
        raise CanvasMVPError("El blueprint todavía contiene decisiones docentes pendientes.")
    required_terms = (blueprint.get("course_identity") or {}).get("required_terms") or []
    if not any(str(item).strip() for item in required_terms):
        raise CanvasMVPError("El blueprint requiere términos distintivos de identidad del curso.")
    groups = blueprint.get("assignment_groups") or []
    if sum(float(item.get("weight") or 0) for item in groups) != 100:
        raise CanvasMVPError("Los grupos de evaluación no suman 100%.")
    assignments = blueprint.get("assignments") or []
    group_names = {str(item.get("name") or "") for item in groups}
    unknown_groups = {
        str(item.get("group"))
        for item in assignments
        if item.get("group") and str(item.get("group")) not in group_names
    }
    if unknown_groups:
        raise CanvasMVPError(f"Hay grupos de evaluación desconocidos: {sorted(unknown_groups)}")
    assignment_keys = [str(item.get("key") or "") for item in assignments]
    if len(assignment_keys) != len(set(assignment_keys)):
        raise CanvasMVPError("El blueprint contiene claves de actividad duplicadas.")
    quizzes = quiz_assignments(blueprint)
    if len(quizzes) != 1:
        raise CanvasMVPError("El MVP portable requiere exactamente un Classic Quiz por perfil.")
    for quiz in quizzes:
        questions = quiz.get("quiz_settings", {}).get("questions") or []
        if not questions:
            raise CanvasMVPError("El quiz del perfil no contiene preguntas.")
        names = [str(item.get("name") or "") for item in questions]
        if any(not name for name in names) or len(names) != len(set(names)):
            raise CanvasMVPError("Cada pregunta del quiz requiere un nombre único.")
        question_points = sum(float(item.get("points") or 0) for item in questions)
        if question_points != float(quiz.get("points") or 0):
            raise CanvasMVPError("Los puntos de las preguntas no coinciden con los puntos del quiz.")
    page_names = [
        str(page)
        for module in blueprint.get("modules") or []
        for page in module.get("pages") or []
    ]
    if len(page_names) != len(set(page_names)):
        raise CanvasMVPError("El blueprint contiene títulos de página duplicados.")
    unknown = {
        key
        for module in blueprint.get("modules") or []
        for key in module.get("assignments") or []
        if key not in assignment_keys
    }
    if unknown:
        raise CanvasMVPError(f"Hay actividades desconocidas en los módulos: {sorted(unknown)}")
    assignments_by_key = {str(item.get("key") or ""): item for item in assignments}
    for group in groups:
        components = group.get("components") or []
        if not components:
            continue
        component_weight = sum(
            float(item.get("course_weight_percent") or 0) for item in components
        )
        if component_weight != float(group.get("weight") or 0):
            raise CanvasMVPError(
                f"El desglose de componentes no coincide con el peso de {group.get('name')}."
            )
        for component in components:
            key = str(component.get("assignment_key") or "")
            assignment = assignments_by_key.get(key)
            if not assignment:
                raise CanvasMVPError(f"El grupo referencia una actividad desconocida: {key}")
            if assignment.get("group") != group.get("name"):
                raise CanvasMVPError(f"La actividad {key} no pertenece al grupo declarado.")
            if float(assignment.get("course_weight_percent") or 0) != float(
                component.get("course_weight_percent") or 0
            ):
                raise CanvasMVPError(f"La incidencia de {key} no coincide con su componente.")
    group_assignments = [
        item
        for item in assignments
        if item.get("group_assignment") is True
        or "equipo" in normalized(str(item.get("mode") or ""))
    ]
    if group_assignments and not blueprint.get("team_group_category"):
        raise CanvasMVPError("Hay tareas grupales, pero falta team_group_category.")


def policy_summary(blueprint: dict[str, Any], key: str) -> str:
    for policy in blueprint.get("course_policies") or []:
        if policy.get("key") == key:
            return str(policy.get("summary") or "")
    return ""


def page_body(blueprint: dict[str, Any], module: dict[str, Any], title: str) -> str:
    notes: list[str] = list((blueprint.get("page_notes") or {}).get(title) or [])
    if title == "Programa, calendario y ruta del curso":
        notes.append(
            f"Período: {blueprint.get('course_dates', {}).get('start')} a "
            f"{blueprint.get('course_dates', {}).get('end')}."
        )
        notes.append(policy_summary(blueprint, "demo_day"))
    elif title == "Aprender y trabajar con IA":
        notes.append(policy_summary(blueprint, "ai_access"))
    elif title == "Datos, privacidad, accesibilidad y alternativas de herramientas":
        notes.append(policy_summary(blueprint, "data_handling"))
    elif title == "Metodología y evaluación del Digital Innovation Studio":
        notes.extend(
            f"{item.get('name')}: {item.get('weight')}%."
            for item in blueprint.get("assignment_groups") or []
        )
        notes.extend(
            [policy_summary(blueprint, "late_recovery"), policy_summary(blueprint, "team_formation")]
        )
    clean_notes = [item for item in notes if item]
    note_html = "".join(f"<li>{escape(item)}</li>" for item in clean_notes)
    ra = ", ".join(str(item) for item in module.get("ra") or [])
    return (
        '<div style="border-left:4px solid #1f4e79;padding:12px;background:#f5f8fb">'
        "<strong>Borrador no publicado.</strong> Completar y revisar antes de hacerlo visible."
        "</div>"
        f"<h2>{escape(title)}</h2>"
        f"<p><strong>Módulo:</strong> {escape(str(module.get('name') or ''))}</p>"
        f"<p><strong>Sesión:</strong> {escape(str(module.get('session') or ''))}</p>"
        f"<p><strong>Resultados de aprendizaje:</strong> {escape(ra)}</p>"
        + (f"<h3>Definiciones vigentes</h3><ul>{note_html}</ul>" if note_html else "")
        + "<h3>Propósito</h3><p>Explicar el propósito de esta etapa y su relación con el proyecto integrador.</p>"
        "<h3>Antes de comenzar</h3><p>Revisar recursos, datos permitidos y criterios de trabajo.</p>"
        "<h3>Actividad</h3><p>Incorporar aquí las instrucciones, recursos y evidencias de aprendizaje.</p>"
        "<h3>Cierre y transferencia</h3><p>Registrar decisiones, evidencia, límites y próximos pasos.</p>"
    )


def assignment_description(blueprint: dict[str, Any], assignment: dict[str, Any]) -> str:
    ra = ", ".join(str(item) for item in assignment.get("ra") or [])
    weight = assignment.get("course_weight_percent")
    weight_line = f"<li><strong>Incidencia:</strong> {weight}% del curso.</li>" if weight else ""
    return (
        '<div style="border-left:4px solid #1f4e79;padding:12px;background:#f5f8fb">'
        "<strong>Borrador no publicado.</strong> Revisar instrucciones y rúbrica antes de publicar."
        "</div><ul>"
        f"<li><strong>Modalidad:</strong> {escape(str(assignment.get('mode') or ''))}</li>"
        f"<li><strong>RA:</strong> {escape(ra)}</li>"
        f"<li><strong>Uso de IA:</strong> {escape(str(assignment.get('iag_level') or ''))}</li>"
        f"{weight_line}"
        "</ul>"
        f"<h3>Evidencia esperada</h3><p>{escape(str(assignment.get('evidence') or ''))}</p>"
        "<h3>Atrasos y recuperación</h3>"
        f"<p>{escape(policy_summary(blueprint, 'late_recovery'))}</p>"
    )


def question_payload(question: dict[str, Any], index: int) -> list[tuple[str, Any]]:
    prompt = str(question.get("prompt") or "")
    max_words = question.get("max_words")
    if max_words:
        prompt += f" Extensión máxima: {max_words} palabras."
    source_type = str(question.get("type") or "essay")
    canvas_type = {
        "multiple_choice": "multiple_choice_question",
        "true_false": "true_false_question",
    }.get(source_type, "essay_question")
    data: list[tuple[str, Any]] = [
        ("question[question_name]", str(question.get("name") or f"Pregunta {index + 1}")),
        ("question[question_text]", f"<p>{escape(prompt)}</p>"),
        ("question[question_type]", canvas_type),
        ("question[position]", index + 1),
        ("question[points_possible]", float(question.get("points") or 0)),
    ]
    if source_type == "multiple_choice":
        for option_index, option in enumerate(question.get("options") or []):
            data.append(
                (f"question[answers][{option_index}][answer_text]", str(option))
            )
            data.append((f"question[answers][{option_index}][answer_weight]", 100))
    elif source_type == "true_false":
        data.extend(
            [
                ("question[answers][0][answer_text]", "True"),
                ("question[answers][0][answer_weight]", 100),
                ("question[answers][1][answer_text]", "False"),
                ("question[answers][1][answer_weight]", 0),
            ]
        )
    return data


def record(
    operations: list[dict[str, Any]],
    kind: str,
    name: str,
    action: str,
    object_id: Any,
) -> None:
    operations.append(
        {"kind": kind, "name": name, "action": action, "id": object_id}
    )


def require_unpublished(item: dict[str, Any], kind: str, name: str) -> None:
    if item.get("published") is True:
        raise CanvasMVPError(
            f"Se encontró {kind} ya publicado con el nombre objetivo: {name}. Se detuvo."
        )


def apply_blueprint(
    client: CanvasWriteClient,
    course_id: int,
    blueprint: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    operations: list[dict[str, Any]] = []
    course = client.get_json(f"/api/v1/courses/{course_id}")
    if not isinstance(course, dict) or int(course.get("id") or 0) != course_id:
        raise CanvasMVPError("Canvas no devolvió el curso confirmado.")
    identity = blueprint.get("course_identity") or {}
    required_terms = [
        normalized(str(item)) for item in identity.get("required_terms") or [] if str(item).strip()
    ]
    course_label = normalized(
        f"{course.get('name') or ''} {course.get('course_code') or ''}"
    )
    missing_terms = [term for term in required_terms if term not in course_label]
    if missing_terms:
        raise CanvasMVPError(
            "La identidad del curso no coincide con el perfil; faltan términos requeridos: "
            + ", ".join(missing_terms)
        )

    if not course.get("apply_assignment_group_weights"):
        updated = client.put_json(
            f"/api/v1/courses/{course_id}",
            {"course[apply_assignment_group_weights]": "true"},
            "activar ponderación por grupos",
        )
        if not updated.get("apply_assignment_group_weights"):
            raise CanvasMVPError("Canvas no confirmó la ponderación por grupos.")
        record(operations, "course_setting", "Ponderación por grupos", "updated", course_id)
    else:
        record(operations, "course_setting", "Ponderación por grupos", "reused", course_id)

    existing_groups = client.get_paginated(
        f"/api/v1/courses/{course_id}/assignment_groups"
    )
    groups_by_name = unique_map(existing_groups, "name", "grupos de evaluación")
    group_ids: dict[str, int] = {}
    next_group_position = max(
        [int(item.get("position") or 0) for item in existing_groups] + [0]
    ) + 1
    for offset, group in enumerate(blueprint.get("assignment_groups") or []):
        name = str(group.get("name") or "")
        existing = groups_by_name.get(normalized(name))
        if existing:
            if float(existing.get("group_weight") or 0) != float(group.get("weight") or 0):
                raise CanvasMVPError(f"El grupo existente tiene un peso distinto: {name}")
            group_ids[name] = int(existing["id"])
            record(operations, "assignment_group", name, "reused", existing.get("id"))
            continue
        created = client.post_json(
            f"/api/v1/courses/{course_id}/assignment_groups",
            {
                "name": name,
                "position": next_group_position + offset,
                "group_weight": group.get("weight"),
            },
            f"crear grupo de evaluación {name}",
        )
        group_ids[name] = int(created["id"])
        groups_by_name[normalized(name)] = created
        record(operations, "assignment_group", name, "created", created.get("id"))

    zero_groups = [
        item for item in existing_groups if float(item.get("group_weight") or 0) == 0
    ]
    preferred_formative = next(
        (item for item in zero_groups if normalized(str(item.get("name"))) == "tareas"),
        zero_groups[0] if zero_groups else None,
    )
    if preferred_formative is None:
        preferred_formative = client.post_json(
            f"/api/v1/courses/{course_id}/assignment_groups",
            {
                "name": "Actividades formativas",
                "position": next_group_position + len(group_ids),
                "group_weight": 0,
            },
            "crear grupo formativo sin ponderación",
        )
        record(
            operations,
            "assignment_group",
            "Actividades formativas",
            "created",
            preferred_formative.get("id"),
        )
    formative_group_id = int(preferred_formative["id"])

    category_spec = blueprint.get("team_group_category") or {}
    category_name = str(category_spec.get("name") or "Equipos interdisciplinarios")
    categories = client.get_paginated(
        f"/api/v1/courses/{course_id}/group_categories",
        params={"collaboration_state": "all"},
    )
    category_by_name = unique_map(categories, "name", "categorías de equipos")
    category = category_by_name.get(normalized(category_name))
    if category:
        record(operations, "group_category", category_name, "reused", category.get("id"))
    else:
        category = client.post_json(
            f"/api/v1/courses/{course_id}/group_categories",
            {"name": category_name},
            f"crear categoría de equipos {category_name}",
        )
        record(operations, "group_category", category_name, "created", category.get("id"))
    group_category_id = int(category["id"])

    assignments_blueprint = {
        str(item.get("key")): item for item in blueprint.get("assignments") or []
    }
    quiz_spec = quiz_assignments(blueprint)[0]
    quiz_key = str(quiz_spec.get("key") or "")
    quiz_name = str(quiz_spec.get("name") or "")
    quizzes = client.get_paginated(f"/api/v1/courses/{course_id}/quizzes")
    quiz_by_name = unique_map(quizzes, "title", "quizzes")
    quiz = quiz_by_name.get(normalized(quiz_name))
    quiz_group_id = group_ids[str(quiz_spec.get("group"))]
    if quiz:
        require_unpublished(quiz, "quiz", quiz_name)
        if int(quiz.get("assignment_group_id") or 0) != quiz_group_id:
            raise CanvasMVPError("El quiz existente pertenece a otro grupo de evaluación.")
        record(operations, "quiz", quiz_name, "reused", quiz.get("id"))
    else:
        quiz_data = {
            "quiz[title]": quiz_name,
            "quiz[description]": assignment_description(blueprint, quiz_spec),
            "quiz[quiz_type]": "assignment",
            "quiz[assignment_group_id]": quiz_group_id,
            "quiz[time_limit]": int(
                quiz_spec.get("quiz_settings", {}).get("time_limit_minutes") or 15
            ),
            "quiz[shuffle_answers]": "false",
            "quiz[allowed_attempts]": int(
                quiz_spec.get("quiz_settings", {}).get("attempts") or 1
            ),
            "quiz[show_correct_answers]": "false",
            "quiz[due_at]": to_canvas_iso(
                str(quiz_spec.get("due_local")), str(blueprint.get("timezone"))
            ),
            "quiz[unlock_at]": to_canvas_iso(
                str(quiz_spec.get("unlock_local")), str(blueprint.get("timezone"))
            ),
            "quiz[published]": "false",
        }
        quiz = client.post_json(
            f"/api/v1/courses/{course_id}/quizzes",
            quiz_data,
            f"crear quiz {quiz_name}",
        )
        require_unpublished(quiz, "quiz", quiz_name)
        record(operations, "quiz", quiz_name, "created", quiz.get("id"))

    quiz_id = int(quiz["id"])
    questions = client.get_paginated(
        f"/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions"
    )
    question_by_name = unique_map(questions, "question_name", "preguntas del quiz")
    question_specs = quiz_spec.get("quiz_settings", {}).get("questions") or []
    for index, question in enumerate(question_specs):
        name = str(question.get("name") or f"Pregunta {index + 1}")
        existing = question_by_name.get(normalized(name))
        if existing:
            record(operations, "quiz_question", name, "reused", existing.get("id"))
            continue
        created = client.post_json(
            f"/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions",
            question_payload(question, index),
            f"crear pregunta {name}",
        )
        record(operations, "quiz_question", name, "created", created.get("id"))

    quiz_assignment_id = quiz.get("assignment_id")
    if not quiz_assignment_id:
        raise CanvasMVPError("Canvas no devolvió la tarea asociada al quiz.")
    quiz_assignment = client.get_json(
        f"/api/v1/courses/{course_id}/assignments/{quiz_assignment_id}"
    )
    if not isinstance(quiz_assignment, dict):
        raise CanvasMVPError("Canvas no devolvió la tarea asociada al quiz.")
    quiz_points = float(quiz_spec.get("points") or 0)
    if float(quiz_assignment.get("points_possible") or 0) != quiz_points:
        quiz_assignment = client.put_json(
            f"/api/v1/courses/{course_id}/assignments/{quiz_assignment_id}",
            {
                "assignment[points_possible]": quiz_points,
                "assignment[published]": "false",
                "assignment[notify_of_update]": "false",
            },
            f"asignar {quiz_points:g} puntos al quiz",
        )
        require_unpublished(quiz_assignment, "tarea de quiz", quiz_name)
        if float(quiz_assignment.get("points_possible") or 0) != quiz_points:
            raise CanvasMVPError("Canvas no confirmó los puntos del quiz.")
        record(
            operations,
            "quiz_points",
            quiz_name,
            "updated",
            quiz_assignment_id,
        )

    existing_assignments = client.get_paginated(
        f"/api/v1/courses/{course_id}/assignments"
    )
    assignments_by_name = unique_map(existing_assignments, "name", "tareas")
    assignment_objects: dict[str, dict[str, Any]] = {
        quiz_key: {
            "id": quiz_assignment_id,
            "quiz_id": quiz_id,
            "name": quiz_name,
            "published": quiz.get("published"),
        }
    }
    for key, assignment in assignments_blueprint.items():
        if key == quiz_key:
            continue
        name = str(assignment.get("name") or "")
        group_name = assignment.get("group")
        assignment_group_id = (
            group_ids[str(group_name)] if group_name else formative_group_id
        )
        existing = assignments_by_name.get(normalized(name))
        is_team = assignment.get("group_assignment") is True or "equipo" in normalized(
            str(assignment.get("mode") or "")
        )
        if existing:
            require_unpublished(existing, "tarea", name)
            if float(existing.get("points_possible") or 0) != float(
                assignment.get("points") or 0
            ):
                raise CanvasMVPError(f"La tarea existente tiene puntos distintos: {name}")
            if int(existing.get("assignment_group_id") or 0) != assignment_group_id:
                raise CanvasMVPError(f"La tarea existente pertenece a otro grupo: {name}")
            assignment_object = existing
            record(operations, "assignment", name, "reused", existing.get("id"))
        else:
            data: list[tuple[str, Any]] = [
                ("assignment[name]", name),
                ("assignment[description]", assignment_description(blueprint, assignment)),
                ("assignment[points_possible]", assignment.get("points") or 0),
                ("assignment[grading_type]", "points"),
                ("assignment[assignment_group_id]", assignment_group_id),
                ("assignment[published]", "false"),
                ("assignment[notify_of_update]", "false"),
            ]
            if assignment.get("kind") == "formative":
                data.append(("assignment[omit_from_final_grade]", "true"))
            if is_team:
                data.append(("assignment[group_category_id]", group_category_id))
            submission_types = assignment.get("submission_types") or [
                "online_text_entry",
                "online_url",
                "online_upload",
            ]
            data.extend(
                ("assignment[submission_types][]", value) for value in submission_types
            )
            assignment_object = client.post_json(
                f"/api/v1/courses/{course_id}/assignments",
                data,
                f"crear tarea {name}",
            )
            require_unpublished(assignment_object, "tarea", name)
            assignments_by_name[normalized(name)] = assignment_object
            record(
                operations,
                "assignment",
                name,
                "created",
                assignment_object.get("id"),
            )
        expected_due_at = to_canvas_iso(
            str(assignment.get("due_local")), str(blueprint.get("timezone"))
        )
        if assignment_object.get("due_at") != expected_due_at:
            assignment_object = client.put_json(
                f"/api/v1/courses/{course_id}/assignments/{assignment_object.get('id')}",
                {
                    "assignment[due_at]": expected_due_at,
                    "assignment[notify_of_update]": "false",
                },
                f"asignar fecha a {name}",
            )
            if assignment_object.get("due_at") != expected_due_at:
                raise CanvasMVPError(f"Canvas no confirmó la fecha de {name}.")
            record(
                operations,
                "assignment_date",
                name,
                "updated",
                assignment_object.get("id"),
            )
        assignment_objects[key] = assignment_object

    existing_pages = client.get_paginated(f"/api/v1/courses/{course_id}/pages")
    pages_by_name = unique_map(existing_pages, "title", "páginas")
    page_objects: dict[str, dict[str, Any]] = {}
    for module in blueprint.get("modules") or []:
        for title_value in module.get("pages") or []:
            title = str(title_value)
            existing = pages_by_name.get(normalized(title))
            if existing:
                require_unpublished(existing, "página", title)
                page_objects[title] = existing
                record(operations, "page", title, "reused", existing.get("page_id"))
                continue
            created = client.post_json(
                f"/api/v1/courses/{course_id}/pages",
                {
                    "wiki_page[title]": title,
                    "wiki_page[body]": page_body(blueprint, module, title),
                    "wiki_page[editing_roles]": "teachers",
                    "wiki_page[notify_of_update]": "false",
                    "wiki_page[published]": "false",
                },
                f"crear página {title}",
            )
            require_unpublished(created, "página", title)
            page_objects[title] = created
            pages_by_name[normalized(title)] = created
            record(operations, "page", title, "created", created.get("page_id"))

    existing_modules = client.get_paginated(f"/api/v1/courses/{course_id}/modules")
    modules_by_name = unique_map(existing_modules, "name", "módulos")
    first_position = max(
        [int(item.get("position") or 0) for item in existing_modules] + [0]
    ) + 1
    module_objects: dict[str, dict[str, Any]] = {}
    for module in blueprint.get("modules") or []:
        module_name = str(module.get("name") or "")
        existing = modules_by_name.get(normalized(module_name))
        if existing:
            require_unpublished(existing, "módulo", module_name)
            canvas_module = existing
            record(operations, "module", module_name, "reused", existing.get("id"))
        else:
            canvas_module = client.post_json(
                f"/api/v1/courses/{course_id}/modules",
                {
                    "module[name]": module_name,
                    "module[position]": first_position + int(module.get("position") or 0),
                    "module[require_sequential_progress]": "false",
                    "module[published]": "false",
                },
                f"crear módulo {module_name}",
            )
            require_unpublished(canvas_module, "módulo", module_name)
            modules_by_name[normalized(module_name)] = canvas_module
            record(operations, "module", module_name, "created", canvas_module.get("id"))
        module_objects[module_name] = canvas_module
        module_id = int(canvas_module["id"])
        existing_items = client.get_paginated(
            f"/api/v1/courses/{course_id}/modules/{module_id}/items"
        )
        items_by_name = unique_map(existing_items, "title", f"elementos de {module_name}")
        desired_items: list[tuple[str, str, Any]] = []
        for title_value in module.get("pages") or []:
            title = str(title_value)
            desired_items.append((title, "Page", page_objects[title].get("url")))
        for key in module.get("assignments") or []:
            assignment = assignments_blueprint[str(key)]
            title = str(assignment.get("name") or "")
            if key == quiz_key:
                desired_items.append((title, "Quiz", quiz_id))
            else:
                desired_items.append((title, "Assignment", assignment_objects[str(key)].get("id")))
        for position, (title, item_type, reference) in enumerate(desired_items, start=1):
            existing_item = items_by_name.get(normalized(title))
            if existing_item:
                require_unpublished(existing_item, "elemento de módulo", title)
                record(
                    operations,
                    "module_item",
                    f"{module_name} / {title}",
                    "reused",
                    existing_item.get("id"),
                )
                continue
            data: dict[str, Any] = {
                "module_item[title]": title,
                "module_item[type]": item_type,
                "module_item[position]": position,
                "module_item[published]": "false",
            }
            if item_type == "Page":
                data["module_item[page_url]"] = reference
            else:
                data["module_item[content_id]"] = reference
            created_item = client.post_json(
                f"/api/v1/courses/{course_id}/modules/{module_id}/items",
                data,
                f"agregar {title} a {module_name}",
            )
            require_unpublished(created_item, "elemento de módulo", title)
            record(
                operations,
                "module_item",
                f"{module_name} / {title}",
                "created",
                created_item.get("id"),
            )

    verification = verify_blueprint(client, course_id, blueprint)
    return operations, verification


def verify_blueprint(
    client: CanvasWriteClient,
    course_id: int,
    blueprint: dict[str, Any],
) -> dict[str, Any]:
    course = client.get_json(f"/api/v1/courses/{course_id}")
    groups = client.get_paginated(f"/api/v1/courses/{course_id}/assignment_groups")
    pages = client.get_paginated(f"/api/v1/courses/{course_id}/pages")
    assignments = client.get_paginated(f"/api/v1/courses/{course_id}/assignments")
    modules = client.get_paginated(f"/api/v1/courses/{course_id}/modules")
    quizzes = client.get_paginated(f"/api/v1/courses/{course_id}/quizzes")
    categories = client.get_paginated(
        f"/api/v1/courses/{course_id}/group_categories",
        params={"collaboration_state": "all"},
    )
    if not isinstance(course, dict) or not course.get("apply_assignment_group_weights"):
        raise CanvasMVPError("La verificación no encontró ponderación por grupos activa.")
    group_map = unique_map(groups, "name", "grupos durante verificación")
    page_map = unique_map(pages, "title", "páginas durante verificación")
    assignment_map = unique_map(assignments, "name", "tareas durante verificación")
    module_map = unique_map(modules, "name", "módulos durante verificación")
    quiz_map = unique_map(quizzes, "title", "quizzes durante verificación")
    category_map = unique_map(categories, "name", "categorías durante verificación")
    for group in blueprint.get("assignment_groups") or []:
        item = group_map.get(normalized(str(group.get("name") or "")))
        if not item or float(item.get("group_weight") or 0) != float(group.get("weight") or 0):
            raise CanvasMVPError("Falló la verificación de grupos de evaluación.")
    for module in blueprint.get("modules") or []:
        item = module_map.get(normalized(str(module.get("name") or "")))
        if not item:
            raise CanvasMVPError(f"Falta el módulo {module.get('name')}.")
        require_unpublished(item, "módulo", str(module.get("name") or ""))
        module_items = client.get_paginated(
            f"/api/v1/courses/{course_id}/modules/{item.get('id')}/items"
        )
        expected = len(module.get("pages") or []) + len(module.get("assignments") or [])
        target_titles = {
            normalized(str(value))
            for value in (module.get("pages") or [])
        } | {
            normalized(str(next(a.get("name") for a in blueprint.get("assignments") or [] if a.get("key") == key)))
            for key in module.get("assignments") or []
        }
        found = [item for item in module_items if normalized(str(item.get("title") or "")) in target_titles]
        if len(found) != expected or any(item.get("published") is True for item in found):
            raise CanvasMVPError(f"Falló la verificación de elementos en {module.get('name')}.")
    target_pages = {
        str(page)
        for module in blueprint.get("modules") or []
        for page in module.get("pages") or []
    }
    for title in target_pages:
        item = page_map.get(normalized(title))
        if not item:
            raise CanvasMVPError(f"Falta la página {title}.")
        require_unpublished(item, "página", title)
    for assignment in blueprint.get("assignments") or []:
        name = str(assignment.get("name") or "")
        item = assignment_map.get(normalized(name))
        if not item:
            raise CanvasMVPError(f"Falta la tarea o quiz {name}.")
        require_unpublished(item, "tarea", name)
    quiz_spec = quiz_assignments(blueprint)[0]
    quiz_name = str(quiz_spec.get("name") or "")
    quiz = quiz_map.get(normalized(quiz_name))
    if not quiz:
        raise CanvasMVPError("Falta el quiz individual.")
    require_unpublished(quiz, "quiz", quiz_name)
    questions = client.get_paginated(
        f"/api/v1/courses/{course_id}/quizzes/{quiz.get('id')}/questions"
    )
    expected_questions = quiz_spec.get("quiz_settings", {}).get("questions") or []
    expected_names = {normalized(str(item.get("name") or "")) for item in expected_questions}
    target_questions = [
        q
        for q in questions
        if normalized(str(q.get("question_name") or ""))
        in expected_names
    ]
    expected_points = float(quiz_spec.get("points") or 0)
    if len(target_questions) != len(expected_questions):
        raise CanvasMVPError("El quiz no contiene todas las preguntas esperadas.")
    if sum(float(item.get("points_possible") or 0) for item in target_questions) != expected_points:
        raise CanvasMVPError("Las preguntas del quiz no suman los puntos esperados.")
    quiz_assignment = assignment_map.get(normalized(quiz_name))
    if not quiz_assignment or float(quiz_assignment.get("points_possible") or 0) != expected_points:
        raise CanvasMVPError("La tarea asociada al quiz no tiene los puntos esperados.")
    category_name = str(blueprint.get("team_group_category", {}).get("name") or "")
    if normalized(category_name) not in category_map:
        raise CanvasMVPError("Falta la categoría de equipos interdisciplinarios.")
    return {
        "course_id": course_id,
        "assignment_group_weights_enabled": True,
        "target_modules": len(blueprint.get("modules") or []),
        "target_pages": len(target_pages),
        "target_assignments_and_quizzes": len(blueprint.get("assignments") or []),
        "target_assignment_groups": len(blueprint.get("assignment_groups") or []),
        "quiz_questions": len(expected_questions),
        "quiz_points": expected_points,
        "team_group_category": category_name,
        "all_target_objects_unpublished": True,
    }


def render_apply_report(report: dict[str, Any]) -> str:
    verification = report.get("verification") or {}
    operations = report.get("operations") or []
    created = [item for item in operations if item.get("action") in {"created", "updated"}]
    reused = [item for item in operations if item.get("action") == "reused"]
    lines = [
        "# Aplicación Canvas · perfil MDS",
        "",
        f"- Estado: **{report.get('status')}**",
        f"- Curso: {report.get('metadata', {}).get('course_id')}",
        f"- Blueprint: {report.get('metadata', {}).get('blueprint_version')}",
        f"- Generado: {report.get('metadata', {}).get('generated_at')}",
        "- Visibilidad: todos los objetos objetivo permanecen no publicados.",
        "",
        "## Verificación",
        "",
    ]
    lines.extend(f"- {key}: {value}" for key, value in verification.items())
    lines.extend(
        [
            "",
            "## Operaciones creadas o ajustadas",
            "",
        ]
    )
    lines.extend(
        f"- {item.get('kind')} · {item.get('name')} · `{item.get('action')}` · ID {item.get('id')}"
        for item in created
    )
    lines.extend(["", "## Objetos reutilizados", ""])
    lines.extend(
        f"- {item.get('kind')} · {item.get('name')} · ID {item.get('id')}"
        for item in reused
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Crear de forma idempotente una estructura MDS no publicada definida por un perfil."
    )
    add_common_arguments(parser)
    parser.add_argument("--blueprint", default=str(DEFAULT_BLUEPRINT))
    parser.add_argument("--confirm-course-id", type=int, required=True)
    parser.add_argument("--confirm-unpublished", action="store_true", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        settings = resolve_settings(args)
        course_id = require_course_id(settings)
        if args.confirm_course_id != course_id:
            raise CanvasMVPError("--confirm-course-id no coincide con el curso configurado.")
        if not args.confirm_unpublished:
            raise CanvasMVPError("Falta --confirm-unpublished.")
        blueprint = read_json_object(Path(args.blueprint), "blueprint")
        validate_blueprint(blueprint)
        token = resolve_token(args, settings)
        client = CanvasWriteClient(settings.base_url, token)
        output_dir = settings.output_root / str(course_id)
        pre_snapshot = collect_snapshot(client, course_id)
        write_json(output_dir / "pre_apply_snapshot.json", pre_snapshot)
        report: dict[str, Any] = {
            "metadata": {
                "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                "course_id": course_id,
                "blueprint_version": blueprint.get("version"),
                "mode": "apply_unpublished",
            },
            "status": "running",
            "operations": [],
            "verification": {},
        }
        try:
            operations, verification = apply_blueprint(client, course_id, blueprint)
            report["operations"] = operations
            report["verification"] = verification
            report["status"] = "completed"
        except Exception as exc:
            report["status"] = "failed_retriable"
            report["error"] = f"{type(exc).__name__}: {exc}"
            write_json(output_dir / "apply_unpublished_latest.json", report)
            (output_dir / "apply_unpublished_latest.md").write_text(
                render_apply_report(report), encoding="utf-8"
            )
            raise
        write_json(output_dir / "apply_unpublished_latest.json", report)
        (output_dir / "apply_unpublished_latest.md").write_text(
            render_apply_report(report), encoding="utf-8"
        )
        post_snapshot = collect_snapshot(client, course_id)
        write_json(output_dir / "snapshot_latest.json", post_snapshot)
        print(f"Aplicación: {output_dir.resolve() / 'apply_unpublished_latest.md'}")
        print("Estado: completed")
        print("Visibilidad: todos los objetos objetivo no publicados")
        return 0
    except (CanvasMVPError, PermissionError, FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
