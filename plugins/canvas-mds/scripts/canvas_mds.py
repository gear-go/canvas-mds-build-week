from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import quote, urljoin, urlsplit

import requests

from process_evidence import process_metrics


DEFAULT_BASE_URL = "https://udd.instructure.com"
DEFAULT_CONFIG = Path(".canvas/local.json")
DEFAULT_OUTPUT_ROOT = Path(".canvas/reports")
DEFAULT_BLUEPRINT = Path(__file__).resolve().parent.parent / "assets" / "profiles" / "entornos-digitales-2026.json"
ALLOWED_STATUSES = {"cumple", "no_cumple", "requiere_revision", "sin_permiso"}


class CanvasMVPError(RuntimeError):
    pass


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data.strip())


def html_to_text(value: str | None) -> str:
    parser = _TextExtractor()
    parser.feed(value or "")
    return " ".join(parser.parts)


def normalized(value: str | None) -> str:
    text = unicodedata.normalize("NFD", value or "")
    return "".join(char for char in text if unicodedata.category(char) != "Mn").lower()


def contains(text: str, *patterns: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def select_fields(source: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    return {field: source.get(field) for field in fields}


@dataclass(frozen=True)
class Settings:
    base_url: str
    course_id: int | None
    output_root: Path
    keyring_service: str
    keyring_account: str


def read_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CanvasMVPError(f"No se pudo leer la configuración {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise CanvasMVPError(f"La configuración {path} debe ser un objeto JSON.")
    return data


def resolve_settings(args: argparse.Namespace) -> Settings:
    config = read_config(Path(args.config))
    base_url = str(args.base_url or config.get("base_url") or DEFAULT_BASE_URL).rstrip("/")
    course_value = args.course_id if args.course_id is not None else config.get("course_id")
    course_id = int(course_value) if course_value not in (None, "") else None
    output_root = Path(args.output_root or config.get("output_root") or DEFAULT_OUTPUT_ROOT)
    return Settings(
        base_url=base_url,
        course_id=course_id,
        output_root=output_root,
        keyring_service=str(
            args.keyring_service or config.get("keyring_service") or "canvas-docencia-mds"
        ),
        keyring_account=str(args.keyring_account or config.get("keyring_account") or ""),
    )


def resolve_token(args: argparse.Namespace, settings: Settings) -> str:
    token = os.getenv("CANVAS_API_TOKEN", "").strip()
    if token:
        return token

    if settings.keyring_account:
        try:
            import keyring  # type: ignore
        except ImportError:
            keyring = None
        if keyring is not None:
            token = (keyring.get_password(settings.keyring_service, settings.keyring_account) or "").strip()
            if token:
                return token

    if args.token_file:
        path = Path(args.token_file)
        try:
            token = path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise CanvasMVPError(f"No se pudo leer el archivo transitorio de token: {path}") from exc
        if token:
            print(
                "ADVERTENCIA: se usó un archivo de token solo como compatibilidad transitoria; "
                "migrar a CANVAS_API_TOKEN o keyring.",
                file=sys.stderr,
            )
            return token

    raise CanvasMVPError(
        "No hay token disponible. Usar CANVAS_API_TOKEN o configurar keyring. "
        "No pegar el token en el chat."
    )


class CanvasReadOnlyClient:
    def __init__(self, base_url: str, token: str, timeout: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.origin = urlsplit(self.base_url).netloc.lower()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "User-Agent": "canvas-mds-portable-readonly/0.1",
            }
        )

    def _absolute_url(self, endpoint_or_url: str) -> str:
        url = (
            endpoint_or_url
            if endpoint_or_url.startswith(("http://", "https://"))
            else urljoin(self.base_url + "/", endpoint_or_url.lstrip("/"))
        )
        parsed = urlsplit(url)
        if parsed.scheme != "https":
            raise CanvasMVPError("El MVP exige HTTPS para todas las solicitudes Canvas.")
        if parsed.netloc.lower() != self.origin:
            raise CanvasMVPError("Canvas devolvió un enlace paginado fuera del origen autorizado.")
        return url

    def _get_response(
        self,
        endpoint_or_url: str,
        params: dict[str, Any] | None = None,
        max_retries: int = 4,
    ) -> requests.Response:
        url = self._absolute_url(endpoint_or_url)
        backoff = 2.0
        for attempt in range(max_retries + 1):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.timeout,
                    verify=True,
                )
            except requests.RequestException as exc:
                if attempt >= max_retries:
                    raise CanvasMVPError(f"Fallo de red al consultar Canvas: {type(exc).__name__}") from exc
                time.sleep(backoff)
                backoff = min(backoff * 2, 20)
                continue

            if response.status_code == 429 or response.status_code >= 500:
                if attempt >= max_retries:
                    raise CanvasMVPError(f"Canvas no respondió tras reintentos (HTTP {response.status_code}).")
                retry_after = response.headers.get("Retry-After", "")
                wait = float(retry_after) if retry_after.replace(".", "", 1).isdigit() else backoff
                time.sleep(min(wait, 30))
                backoff = min(backoff * 2, 20)
                params = None if endpoint_or_url.startswith("http") else params
                continue

            if response.status_code in (401, 403):
                raise PermissionError(f"Canvas rechazó la lectura (HTTP {response.status_code}).")
            if response.status_code == 404:
                raise FileNotFoundError("El recurso Canvas solicitado no existe o no es visible.")
            try:
                response.raise_for_status()
            except requests.HTTPError as exc:
                raise CanvasMVPError(f"Error Canvas HTTP {response.status_code}.") from exc
            return response
        raise CanvasMVPError("No se pudo completar la lectura de Canvas.")

    def get_json(
        self, endpoint_or_url: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any] | list[dict[str, Any]]:
        response = self._get_response(endpoint_or_url, params=params)
        data = response.json()
        if not isinstance(data, (dict, list)):
            raise CanvasMVPError("Canvas devolvió un formato JSON inesperado.")
        return data

    def get_paginated(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        url = endpoint
        query = dict(params or {})
        query.setdefault("per_page", 100)
        result: list[dict[str, Any]] = []
        while url:
            response = self._get_response(url, params=query)
            data = response.json()
            if not isinstance(data, list):
                raise CanvasMVPError("Se esperaba una lista paginada de Canvas.")
            result.extend(item for item in data if isinstance(item, dict))
            next_link = response.links.get("next", {}).get("url")
            url = str(next_link) if next_link else ""
            query = {}
        return result


def require_course_id(settings: Settings) -> int:
    if settings.course_id is None:
        raise CanvasMVPError("Falta course_id en la configuración o en --course-id.")
    return settings.course_id


def safe_paginated(
    client: CanvasReadOnlyClient,
    endpoint: str,
    permission_issues: list[str],
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    try:
        return client.get_paginated(endpoint, params=params)
    except PermissionError:
        permission_issues.append(endpoint)
        return []


def sanitize_module(module: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, Any]:
    clean_items = []
    for item in items:
        clean = select_fields(
            item,
            ("id", "title", "type", "position", "published", "content_id", "indent"),
        )
        details = item.get("content_details") or {}
        clean["content_details"] = select_fields(
            details,
            ("due_at", "unlock_at", "lock_at", "points_possible"),
        )
        clean_items.append(clean)
    clean_module = select_fields(
        module,
        ("id", "name", "position", "published", "unlock_at", "require_sequential_progress"),
    )
    clean_module["items"] = clean_items
    return clean_module


def sanitize_assignment(assignment: dict[str, Any]) -> dict[str, Any]:
    clean = select_fields(
        assignment,
        (
            "id",
            "name",
            "description",
            "published",
            "points_possible",
            "due_at",
            "unlock_at",
            "lock_at",
            "submission_types",
            "assignment_group_id",
            "group_category_id",
            "grading_type",
            "anonymous_grading",
            "omit_from_final_grade",
        ),
    )
    clean["has_rubric"] = bool(assignment.get("rubric") or assignment.get("rubric_settings"))
    return clean


def collect_snapshot(client: CanvasReadOnlyClient, course_id: int) -> dict[str, Any]:
    permission_issues: list[str] = []
    course_raw = client.get_json(
        f"/api/v1/courses/{course_id}",
        params={"include[]": ["term"]},
    )
    if not isinstance(course_raw, dict):
        raise CanvasMVPError("Canvas no devolvió un curso válido.")

    modules_raw = safe_paginated(client, f"/api/v1/courses/{course_id}/modules", permission_issues)
    modules = []
    for module in modules_raw:
        module_id = module.get("id")
        items = safe_paginated(
            client,
            f"/api/v1/courses/{course_id}/modules/{module_id}/items",
            permission_issues,
            params={"include[]": ["content_details"]},
        )
        modules.append(sanitize_module(module, items))

    pages_raw = safe_paginated(client, f"/api/v1/courses/{course_id}/pages", permission_issues)
    pages: list[dict[str, Any]] = []
    for page in pages_raw:
        clean = select_fields(page, ("page_id", "url", "title", "published", "front_page", "updated_at"))
        title = normalized(str(page.get("title") or ""))
        if page.get("front_page") or contains(title, r"comience aqui", r"bienven", r"inicio", r"start here"):
            slug = quote(str(page.get("url") or ""), safe="")
            try:
                detail = client.get_json(f"/api/v1/courses/{course_id}/pages/{slug}")
            except PermissionError:
                permission_issues.append(f"/api/v1/courses/{course_id}/pages/{slug}")
                detail = {}
            if isinstance(detail, dict):
                clean["body"] = detail.get("body") or ""
        pages.append(clean)

    assignments_raw = safe_paginated(
        client,
        f"/api/v1/courses/{course_id}/assignments",
        permission_issues,
    )
    groups_raw = safe_paginated(
        client,
        f"/api/v1/courses/{course_id}/assignment_groups",
        permission_issues,
    )
    rubrics_raw = safe_paginated(client, f"/api/v1/courses/{course_id}/rubrics", permission_issues)
    tabs_raw = safe_paginated(client, f"/api/v1/courses/{course_id}/tabs", permission_issues)

    course = select_fields(
        course_raw,
        (
            "id",
            "name",
            "course_code",
            "workflow_state",
            "default_view",
            "start_at",
            "end_at",
            "is_public",
            "apply_assignment_group_weights",
            "syllabus_body",
        ),
    )
    term = course_raw.get("term") or {}
    course["term"] = select_fields(term, ("id", "name", "start_at", "end_at"))

    groups = [
        select_fields(group, ("id", "name", "position", "group_weight", "rules"))
        for group in groups_raw
    ]
    rubrics = []
    for rubric in rubrics_raw:
        clean = select_fields(rubric, ("id", "title", "points_possible", "free_form_criterion_comments"))
        clean["criteria_count"] = len(rubric.get("data") or [])
        rubrics.append(clean)

    return {
        "metadata": {
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "mode": "read_only",
            "scope": "estructura sin estudiantes, matrículas, entregas, notas ni analítica individual",
            "course_id": course_id,
            "permission_issues": sorted(set(permission_issues)),
        },
        "course": course,
        "modules": modules,
        "pages": pages,
        "assignments": [sanitize_assignment(item) for item in assignments_raw],
        "assignment_groups": groups,
        "rubrics": rubrics,
        "tabs": [select_fields(tab, ("id", "label", "position", "visibility", "hidden")) for tab in tabs_raw],
    }


def corpus(snapshot: dict[str, Any]) -> str:
    parts = [html_to_text(snapshot.get("course", {}).get("syllabus_body"))]
    for module in snapshot.get("modules", []):
        parts.append(str(module.get("name") or ""))
        parts.extend(str(item.get("title") or "") for item in module.get("items", []))
    for page in snapshot.get("pages", []):
        parts.append(str(page.get("title") or ""))
        parts.append(html_to_text(page.get("body")))
    for assignment in snapshot.get("assignments", []):
        parts.append(str(assignment.get("name") or ""))
        parts.append(html_to_text(assignment.get("description")))
    parts.extend(str(rubric.get("title") or "") for rubric in snapshot.get("rubrics", []))
    return normalized(" ".join(parts))


def is_academic_module(module: dict[str, Any]) -> bool:
    name = normalized(str(module.get("name") or ""))
    return not contains(
        name,
        r"ayuda para profesores",
        r"informacion relevante que debes conocer",
        r"normativas?, servicios y apoyos",
    )


def evaluate_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    course = snapshot.get("course", {})
    modules = snapshot.get("modules", [])
    pages = snapshot.get("pages", [])
    assignments = snapshot.get("assignments", [])
    groups = snapshot.get("assignment_groups", [])
    permission_issues = snapshot.get("metadata", {}).get("permission_issues", [])
    text = corpus(snapshot)
    academic_modules = [module for module in modules if is_academic_module(module)]
    findings: list[dict[str, Any]] = []

    def add(
        criterion_id: str,
        title: str,
        priority: str,
        mode: str,
        status: str,
        evidence: str,
        recommendation: str,
    ) -> None:
        if status not in ALLOWED_STATUSES:
            raise ValueError(f"Estado inválido: {status}")
        findings.append(
            {
                "id": criterion_id,
                "title": title,
                "priority": priority,
                "mode": mode,
                "status": status,
                "evidence": evidence,
                "recommendation": recommendation,
            }
        )

    add(
        "GOV-01",
        "Aplicabilidad formal del programa al MDS",
        "bloqueante",
        "manual",
        "requiere_revision",
        "La guía identifica esta confirmación como pendiente institucional.",
        "Obtener confirmación de coordinación y registrar programa/versión vigente.",
    )

    available = course.get("workflow_state") == "available"
    add(
        "PUB-01",
        "Estado disponible del curso",
        "bloqueante",
        "automatico",
        "cumple" if available else "no_cumple",
        f"workflow_state={course.get('workflow_state')}",
        "Confirmar que el estado corresponde al momento del piloto.",
    )

    start_pages = [
        page
        for page in pages
        if page.get("front_page")
        or contains(normalized(str(page.get("title") or "")), r"comience aqui", r"bienven", r"inicio", r"start here")
    ]
    add(
        "INI-01",
        "Página Comience aquí o equivalente",
        "bloqueante",
        "automatico",
        "cumple" if start_pages else "no_cumple",
        f"Páginas candidatas: {', '.join(str(p.get('title')) for p in start_pages) or 'ninguna'}.",
        "Crear una página inicial y configurarla como puerta de entrada visible.",
    )
    start_text = normalized(" ".join(html_to_text(page.get("body")) for page in start_pages))
    start_groups = {
        "propósito": contains(start_text, r"proposito", r"aprender"),
        "navegación": contains(start_text, r"ruta", r"naveg", r"modulo"),
        "apoyo": contains(start_text, r"apoyo", r"soporte", r"consulta", r"foro"),
        "expectativas": contains(start_text, r"expectativa", r"participa", r"respuesta docente"),
    }
    start_missing = [name for name, present in start_groups.items() if not present]
    add(
        "INI-02",
        "Contenido mínimo de la página inicial",
        "bloqueante",
        "asistido",
        "no_cumple" if not start_pages else "requiere_revision",
        "Componentes no detectados: " + (", ".join(start_missing) if start_missing else "ninguno por palabra clave"),
        "Revisar propósito, ruta, apoyo y expectativas en la página inicial.",
    )

    add(
        "EST-01",
        "Curso organizado mediante módulos",
        "bloqueante",
        "automatico",
        "cumple" if academic_modules else ("sin_permiso" if any("/modules" in item for item in permission_issues) else "no_cumple"),
        f"Módulos totales: {len(modules)}; módulos académicos candidatos: {len(academic_modules)}.",
        "Crear módulos académicos con una secuencia visible y repetible; conservar los apoyos institucionales como soporte.",
    )
    module_names = [normalized(str(module.get("name") or "")) for module in academic_modules]
    patterned = [name for name in module_names if contains(name, r"semana\s*\d+", r"modulo\s*\d+")]
    ratio = len(patterned) / len(module_names) if module_names else 0
    add(
        "EST-02",
        "Nomenclatura consistente de módulos",
        "mejora",
        "automatico",
        "cumple" if modules and ratio >= 0.7 else "no_cumple",
        f"{len(patterned)}/{len(module_names)} módulos siguen Semana/Módulo N.",
        "Normalizar títulos sin perder nombres pedagógicos útiles.",
    )
    module_zero = [
        module
        for module in academic_modules
        if contains(normalized(str(module.get("name") or "")), r"modulo\s*0+\b", r"bienven", r"orienta", r"inicio")
    ]
    add(
        "EST-03",
        "Módulo 00 u orientación inicial",
        "bloqueante",
        "automatico",
        "cumple" if module_zero else "no_cumple",
        f"Candidatos: {', '.join(str(m.get('name')) for m in module_zero) or 'ninguno'}.",
        "Incluir mapa, pauta de presentaciones, reglas IAG y manejo de datos.",
    )

    published_assignments = [item for item in assignments if item.get("published")]
    add(
        "EVA-01",
        "Evaluaciones publicadas detectables",
        "bloqueante",
        "automatico",
        "cumple" if published_assignments else "no_cumple",
        f"Tareas publicadas: {len(published_assignments)} de {len(assignments)}.",
        "Configurar las evaluaciones requeridas antes de validar el curso.",
    )
    ra_assignments = [
        item
        for item in published_assignments
        if contains(
            normalized(html_to_text(item.get("description"))),
            r"resultado[s]? de aprendizaje",
            r"\bra\s*\d+",
        )
    ]
    add(
        "ALI-01",
        "RA visibles en las evaluaciones",
        "bloqueante",
        "asistido",
        "no_cumple" if published_assignments and not ra_assignments else "requiere_revision",
        f"Evaluaciones con referencia detectable a RA: {len(ra_assignments)}/{len(published_assignments)}.",
        "Confirmar que cada evaluación explicita RA, evidencia y criterio coherentes.",
    )

    iag_assignments = [
        item
        for item in published_assignments
        if contains(
            normalized(html_to_text(item.get("description"))),
            r"nivel\s*[abc]\b",
            r"\biag\b",
            r"inteligencia artificial generativa",
            r"contrato.*fase",
        )
    ]
    add(
        "IAG-01",
        "Nivel IAG y contrato por fase",
        "bloqueante",
        "asistido",
        "no_cumple" if published_assignments and not iag_assignments else "requiere_revision",
        f"Evaluaciones con regla IAG detectable: {len(iag_assignments)}/{len(published_assignments)}.",
        "Publicar nivel A/B/C, capacidades permitidas, techo de delegación y declaración.",
    )

    data_visible = contains(text, r"anonimiz", r"datos confidencial", r"clasificacion de datos", r"plataforma autorizada")
    access_visible = contains(text, r"alternativa equivalente", r"sin costo", r"gratuit", r"herramienta institucional")
    add(
        "DAT-01",
        "Reglas de datos y alternativa de acceso",
        "bloqueante",
        "asistido",
        "no_cumple" if not (data_visible and access_visible) else "requiere_revision",
        f"Regla de datos detectable={data_visible}; alternativa de acceso detectable={access_visible}.",
        "Explicitar datos, plataformas, anonimización, herramienta base y alternativa equivalente.",
    )

    rubric_assignments = [item for item in published_assignments if item.get("has_rubric")]
    add(
        "RUB-01",
        "Rúbricas asociadas a tareas publicadas",
        "bloqueante",
        "automatico",
        "cumple" if published_assignments and len(rubric_assignments) == len(published_assignments) else "no_cumple",
        f"Con rúbrica: {len(rubric_assignments)}/{len(published_assignments)}.",
        "Asociar la rúbrica y verificar que sus puntos coincidan con cada tarea.",
    )

    configured_assignments = [
        item
        for item in published_assignments
        if item.get("due_at") and item.get("submission_types")
    ]
    add(
        "ACC-01",
        "Fechas y tipos de entrega configurados",
        "bloqueante",
        "automatico",
        "cumple" if published_assignments and len(configured_assignments) == len(published_assignments) else "no_cumple",
        f"Con fecha y tipo de entrega: {len(configured_assignments)}/{len(published_assignments)}.",
        "Revisar vencimiento, disponibilidad, modalidad, grupos y archivos permitidos.",
    )

    if course.get("apply_assignment_group_weights"):
        total_weight = sum(float(group.get("group_weight") or 0) for group in groups)
        weight_status = "cumple" if abs(total_weight - 100.0) < 0.01 else "no_cumple"
        weight_evidence = f"Ponderación por grupos activa; suma={total_weight:.2f}%."
    else:
        weight_status = "requiere_revision"
        weight_evidence = "Ponderación por grupos no activa; comprobar equivalencia por puntos con el programa."
    add(
        "PON-01",
        "Ponderaciones coherentes con el programa",
        "bloqueante",
        "asistido",
        weight_status,
        weight_evidence.strip(),
        "Verificar presentación breve 30% y componente oral bimestral 70%, o documentar estructura vigente aprobada.",
    )

    oral_items = [
        item
        for item in published_assignments
        if contains(normalized(str(item.get("name") or "")), r"presentacion", r"oral", r"bimestral", r"defensa")
    ]
    oral_text = normalized(" ".join(html_to_text(item.get("description")) for item in oral_items))
    split_visible = contains(oral_text, r"individual") and contains(oral_text, r"grupal", r"grupo")
    add(
        "AUT-01",
        "Evidencia grupal e individual en componente oral",
        "bloqueante",
        "asistido",
        "no_cumple" if oral_items and not split_visible else "requiere_revision",
        f"Evaluaciones orales candidatas={len(oral_items)}; separación textual detectable={split_visible}.",
        "Definir qué se evalúa grupalmente y qué se confirma con preguntas individuales estandarizadas.",
    )

    indicator_patterns = {
        "diagnóstico": (r"diagnost",),
        "diseño de valor": (r"propuesta de valor", r"diseno", r"solucion"),
        "gobernanza/ética": (r"gobern", r"etic", r"privacidad"),
        "implementación": (r"implement", r"adopcion", r"viabilidad"),
        "comunicación": (r"comunica", r"presenta", r"audiencia"),
    }
    detected_indicators = [
        label for label, patterns in indicator_patterns.items() if contains(text, *patterns)
    ]
    add(
        "RA-ENT-01",
        "RA amplio desagregado en indicadores observables",
        "bloqueante",
        "asistido",
        "no_cumple" if len(detected_indicators) < 4 else "requiere_revision",
        f"Indicadores detectados: {', '.join(detected_indicators) or 'ninguno'}.",
        "Confirmar diagnóstico, valor, gobernanza/ética, implementación y comunicación con evidencia observable.",
    )

    traceability = contains(text, r"fuente", r"evidencia", r"afirmacion", r"experimento", r"trazabilidad")
    transfer = contains(text, r"defensa individual", r"pregunta individual", r"transferencia", r"sin iag")
    feedback = contains(text, r"retroaliment", r"feedback", r"borrador", r"hito", r"revision")
    resistance = contains(text, r"prueba de resistencia", r"agente generalista", r"redisen")
    governance = contains(text, r"que automatizar", r"mantener humano", r"rendicion de cuentas", r"escalamiento")
    change_scenario = contains(text, r"incidente", r"presupuesto", r"rechazo de usuarios", r"shock", r"pivot")

    for criterion_id, title, priority, detected, recommendation in [
        ("TRA-01", "Trazabilidad de afirmaciones y decisiones", "bloqueante", traceability, "Exigir fuente, experimento o evidencia exacta para afirmaciones centrales."),
        ("TRF-01", "Transferencia individual", "bloqueante", transfer, "Añadir defensa o cambio de escenario individual con criterio estandarizado."),
        ("FDB-01", "Ciclo de feedback y revisión", "bloqueante", feedback, "Permitir aplicar feedback antes de la calificación final."),
        ("IAR-01", "Prueba de resistencia frente a IA", "bloqueante", resistance, "Registrar herramienta, fecha, resultado y rediseño realizado."),
        ("GOB-ENT-01", "Autoridad y gobernanza humano–IA", "bloqueante", governance, "Hacer explícita autoridad, escalamiento, privacidad, inclusión y rendición de cuentas."),
        ("ESC-01", "Cambio de escenario o pivote", "mejora", change_scenario, "Incorporar incidente, restricción presupuestaria o rechazo de usuarios."),
    ]:
        add(
            criterion_id,
            title,
            priority,
            "asistido",
            "requiere_revision" if detected else "no_cumple",
            f"Evidencia textual detectable={detected}.",
            recommendation,
        )

    add(
        "NAV-01",
        "Vista del estudiante, enlaces y accesibilidad",
        "bloqueante",
        "manual",
        "requiere_revision",
        "La API no reproduce de forma suficiente la experiencia del estudiante.",
        "Recorrer el curso como estudiante y revisar visibilidad, enlaces, encabezados, contraste, alt text y subtítulos.",
    )

    blockers = [item for item in findings if item["priority"] == "bloqueante"]
    failed_blockers = [item for item in blockers if item["status"] == "no_cumple"]
    pending_blockers = [item for item in blockers if item["status"] in ("requiere_revision", "sin_permiso")]
    if failed_blockers:
        overall = "NO_LISTO_PROVISIONAL"
    elif pending_blockers:
        overall = "REQUIERE_REVISION_DOCENTE"
    else:
        overall = "LISTO_PROVISIONAL"

    status_rank = {"no_cumple": 0, "sin_permiso": 1, "requiere_revision": 2, "cumple": 3}
    priority_rank = {"bloqueante": 0, "mejora": 1}
    unresolved = {item["id"]: item for item in findings if item["status"] != "cumple"}
    preferred_roots = [
        "EST-01",
        "EVA-01",
        "GOV-01",
        "INI-02",
        "EST-03",
        "RA-ENT-01",
        "IAG-01",
        "DAT-01",
        "RUB-01",
        "ACC-01",
    ]
    priorities = [unresolved[item_id] for item_id in preferred_roots if item_id in unresolved][:3]
    if len(priorities) < 3:
        already_selected = {item["id"] for item in priorities}
        remaining = sorted(
            (item for item in unresolved.values() if item["id"] not in already_selected),
            key=lambda item: (priority_rank[item["priority"]], status_rank[item["status"]], item["id"]),
        )
        priorities.extend(remaining[: 3 - len(priorities)])

    return {
        "overall": overall,
        "summary": {
            "criteria_total": len(findings),
            "blockers_total": len(blockers),
            "blockers_failed": len(failed_blockers),
            "blockers_pending_review": len(pending_blockers),
            "modules_total": len(modules),
            "academic_modules_detected": len(academic_modules),
            "automatic_passed": sum(
                1 for item in findings if item["mode"] == "automatico" and item["status"] == "cumple"
            ),
        },
        "top_priorities": priorities,
        "findings": findings,
    }


def render_report(snapshot: dict[str, Any], audit: dict[str, Any]) -> str:
    course = snapshot["course"]
    summary = audit["summary"]
    lines = [
        "# Auditoría estructural Canvas · MDS",
        "",
        f"- Curso: {course.get('name')}",
        f"- Canvas course ID: {course.get('id')}",
        f"- Código: {course.get('course_code')}",
        f"- Generado: {snapshot['metadata'].get('generated_at')}",
        "- Alcance: solo estructura; sin estudiantes, matrículas, entregas, notas ni analítica individual.",
        "",
        "## Resultado provisional",
        "",
        f"**{audit['overall']}**",
        "",
        f"- Bloqueantes: {summary['blockers_total']}",
        f"- Bloqueantes no cumplidos: {summary['blockers_failed']}",
        f"- Bloqueantes pendientes de revisión: {summary['blockers_pending_review']}",
        f"- Módulos totales / académicos candidatos: {summary['modules_total']} / {summary['academic_modules_detected']}",
        f"- Controles automáticos cumplidos: {summary['automatic_passed']}",
        "",
        "> El resultado no reemplaza la revisión docente ni la Vista del estudiante.",
        "",
        "## Tres acciones prioritarias",
        "",
    ]
    for index, item in enumerate(audit["top_priorities"], start=1):
        lines.append(f"{index}. **{item['id']} · {item['title']}** — {item['recommendation']}")
        lines.append(f"   Evidencia: {item['evidence']}")

    lines.extend(
        [
            "",
            "## Matriz de hallazgos",
            "",
            "| ID | Prioridad | Tipo | Estado | Criterio | Evidencia |",
            "|---|---|---|---|---|---|",
        ]
    )
    for item in audit["findings"]:
        evidence = str(item["evidence"]).replace("|", "/").replace("\n", " ")
        lines.append(
            f"| {item['id']} | {item['priority']} | {item['mode']} | {item['status']} | "
            f"{item['title']} | {evidence} |"
        )

    issues = snapshot["metadata"].get("permission_issues") or []
    lines.extend(["", "## Permisos parciales", ""])
    if issues:
        lines.extend(f"- Sin permiso para: `{endpoint}`" for endpoint in issues)
    else:
        lines.append("- No se detectaron endpoints estructurales rechazados por permisos.")
    lines.append("")
    return "\n".join(lines)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise CanvasMVPError(f"No se pudo leer {label}: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CanvasMVPError(f"{label.capitalize()} no contiene JSON válido: {path}") from exc
    if not isinstance(payload, dict):
        raise CanvasMVPError(f"{label.capitalize()} debe ser un objeto JSON.")
    return payload


def build_dry_run(snapshot: dict[str, Any], blueprint: dict[str, Any]) -> dict[str, Any]:
    existing_modules = {
        normalized(str(item.get("name") or "")): item for item in snapshot.get("modules", [])
    }
    existing_pages = {
        normalized(str(item.get("title") or "")): item for item in snapshot.get("pages", [])
    }
    existing_assignments = {
        normalized(str(item.get("name") or "")): item for item in snapshot.get("assignments", [])
    }
    existing_groups = {
        normalized(str(item.get("name") or "")): item
        for item in snapshot.get("assignment_groups", [])
    }
    assignment_by_key = {
        str(item.get("key")): item for item in blueprint.get("assignments", [])
    }

    def action_for(name: str, existing: dict[str, dict[str, Any]]) -> str:
        return "review_existing" if normalized(name) in existing else "create_unpublished"

    groups = []
    for group in blueprint.get("assignment_groups", []):
        current = existing_groups.get(normalized(str(group.get("name") or "")))
        action = "create" if current is None else "review_weight"
        groups.append({**group, "action": action, "current_weight": (current or {}).get("group_weight")})

    assignments = []
    for assignment in blueprint.get("assignments", []):
        assignments.append(
            {
                **assignment,
                "action": action_for(str(assignment.get("name") or ""), existing_assignments),
                "published": False,
            }
        )

    modules = []
    proposed_page_names: set[str] = set()
    for module in blueprint.get("modules", []):
        module_pages = []
        for page_name in module.get("pages", []):
            proposed_page_names.add(str(page_name))
            module_pages.append(
                {
                    "name": page_name,
                    "action": action_for(str(page_name), existing_pages),
                    "published": False,
                }
            )
        module_assignments = [
            assignment_by_key[key]
            for key in module.get("assignments", [])
            if key in assignment_by_key
        ]
        modules.append(
            {
                **module,
                "action": action_for(str(module.get("name") or ""), existing_modules),
                "published": False,
                "pages_plan": module_pages,
                "assignments_plan": [
                    {
                        "key": item.get("key"),
                        "name": item.get("name"),
                        "action": action_for(str(item.get("name") or ""), existing_assignments),
                    }
                    for item in module_assignments
                ],
            }
        )

    pages_to_create = sum(
        1
        for module in modules
        for page in module["pages_plan"]
        if page["action"] == "create_unpublished"
    )
    return {
        "metadata": {
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "mode": "dry_run",
            "canvas_mutations": 0,
            "course_id": snapshot.get("course", {}).get("id"),
            "blueprint_version": blueprint.get("version"),
            "source_files": blueprint.get("source_files", []),
        },
        "current": {
            "modules": len(snapshot.get("modules", [])),
            "pages": len(snapshot.get("pages", [])),
            "assignments": len(snapshot.get("assignments", [])),
            "assignment_groups": len(snapshot.get("assignment_groups", [])),
        },
        "proposed": {
            "modules": len(modules),
            "unique_pages": len(proposed_page_names),
            "assignments": len(assignments),
            "summative_assignments": sum(1 for item in assignments if item.get("kind") == "summative"),
            "formative_assignments": sum(1 for item in assignments if item.get("kind") == "formative"),
            "assignment_groups": len(groups),
        },
        "actions": {
            "modules_to_create": sum(1 for item in modules if item["action"] == "create_unpublished"),
            "pages_to_create": pages_to_create,
            "assignments_to_create": sum(
                1 for item in assignments if item["action"] == "create_unpublished"
            ),
            "groups_to_create": sum(1 for item in groups if item["action"] == "create"),
        },
        "assignment_groups": groups,
        "assignments": assignments,
        "modules": modules,
        "learning_outcomes": blueprint.get("learning_outcomes", {}),
        "course_policies": blueprint.get("course_policies", []),
        "manual_decisions": blueprint.get("manual_decisions", []),
        "process_assessment_policy": blueprint.get("process_assessment_policy", {}),
        "pedagogical_redesign": blueprint.get("pedagogical_redesign", {}),
        "process_metrics": (
            process_metrics(blueprint)
            if (blueprint.get("process_assessment_policy") or {}).get("enabled") is True
            else {}
        ),
    }


def render_dry_run(snapshot: dict[str, Any], blueprint: dict[str, Any], plan: dict[str, Any]) -> str:
    course = snapshot.get("course", {})
    current = plan["current"]
    proposed = plan["proposed"]
    actions = plan["actions"]
    lines = [
        f"# Dry-run de construcción Canvas · {blueprint.get('course_profile') or 'perfil MDS'}",
        "",
        "> **No se modificó Canvas.** Este documento contiene únicamente una propuesta de cambios.",
        "",
        f"- Curso Canvas: {course.get('id')} · {course.get('name')}",
        f"- Perfil: {blueprint.get('course_profile')}",
        f"- Período: {blueprint.get('course_dates', {}).get('start')} a {blueprint.get('course_dates', {}).get('end')}",
        f"- Zona horaria: {blueprint.get('timezone')}",
        "- Estado propuesto para objetos nuevos: no publicados.",
        "",
        "## Fuentes",
        "",
    ]
    lines.extend(f"- `{item}`" for item in blueprint.get("source_files", []))
    lines.extend(
        [
            "",
            "## Resumen del diff",
            "",
            "| Objeto | Actual | Propuesto | Por crear |",
            "|---|---:|---:|---:|",
            f"| Módulos | {current['modules']} | {proposed['modules']} | {actions['modules_to_create']} |",
            f"| Páginas únicas | {current['pages']} | {proposed['unique_pages']} | {actions['pages_to_create']} |",
            f"| Tareas | {current['assignments']} | {proposed['assignments']} | {actions['assignments_to_create']} |",
            f"| Grupos de tareas | {current['assignment_groups']} | {proposed['assignment_groups']} | {actions['groups_to_create']} |",
            "",
            str(blueprint.get("structure_note") or "La propuesta se deriva del perfil del curso y debe ser revisada por el equipo docente antes de aplicarse."),
        ]
    )
    metrics = plan.get("process_metrics") or {}
    if metrics:
        diagnosis = (plan.get("pedagogical_redesign") or {}).get("diagnosis") or {}
        lines.extend(
            [
                "",
                "## Rediseño centrado en el proceso",
                "",
                str(diagnosis.get("assessment_validity_problem") or ""),
                "",
                "| Evidencia | Peso aprobado |",
                "|---|---:|",
                f"| Producto final | {metrics.get('product_weight_percent')}% |",
                f"| Proceso de aprendizaje | {metrics.get('process_weight_percent')}% |",
                f"| Evidencia individual | {metrics.get('individual_evidence_weight_percent')}% |",
            ]
        )
    lines.extend(
        [
            "",
            "## Grupos de evaluación",
            "",
            "| Grupo | Peso | Acción | Peso actual si existe |",
            "|---|---:|---|---:|",
        ]
    )
    for group in plan["assignment_groups"]:
        lines.append(
            f"| {group.get('name')} | {group.get('weight')}% | {group.get('action')} | "
            f"{group.get('current_weight') if group.get('current_weight') is not None else '—'} |"
        )

    lines.extend(
        [
            "",
            "## Evaluaciones y checkpoints",
            "",
            "| Actividad | Tipo | Etapa | Alcance | Vence | Grupo/peso | Puntos/incidencia | Modalidad | RA | IAG | Acción |",
            "|---|---|---|---|---|---|---|---|---|---|---|",
        ]
    )
    group_weights = {
        str(group.get("name")): group.get("weight") for group in plan["assignment_groups"]
    }
    for item in plan["assignments"]:
        group_name = item.get("group")
        if group_name:
            group_label = f"{group_name} ({group_weights.get(str(group_name))}%)"
        elif item.get("kind") == "formative":
            group_label = "Formativa (0%)"
        else:
            group_label = "Evidencia individual (sin ponderación independiente definida)"
        points_label = f"{item.get('points')} pts"
        if item.get("course_weight_percent") is not None:
            points_label += f" · {item.get('course_weight_percent')}% del curso"
        lines.append(
            f"| {item.get('name')} | {item.get('kind')} | {item.get('process_stage')} | "
            f"{item.get('evidence_scope')} | {item.get('due_local')} | {group_label} | {points_label} | "
            f"{item.get('mode')} | {', '.join(item.get('ra', []))} | {item.get('iag_level')} | {item.get('action')} |"
        )

    lines.extend(["", "## Arquitectura de módulos", ""])
    for module in plan["modules"]:
        lines.append(
            f"### {module.get('position')} · {module.get('name')} [{module.get('action')}]"
        )
        lines.append("")
        lines.append(f"- Período: {module.get('period')}")
        lines.append(f"- Sesión: {module.get('session')}")
        lines.append(f"- RA: {', '.join(module.get('ra', []))}")
        lines.append("- Páginas:")
        lines.extend(
            f"  - {page.get('name')} — `{page.get('action')}`" for page in module["pages_plan"]
        )
        lines.append("- Actividades:")
        if module["assignments_plan"]:
            lines.extend(
                f"  - {item.get('name')} — `{item.get('action')}`"
                for item in module["assignments_plan"]
            )
        else:
            lines.append("  - Ninguna.")
        lines.append("")

    lines.extend(["## Definiciones docentes incorporadas", ""])
    policies = plan.get("course_policies", [])
    if policies:
        lines.extend(
            f"- **{policy.get('label')}** [{policy.get('status')}]: {policy.get('summary')}"
            for policy in policies
        )
    else:
        lines.append("- Ninguna registrada.")

    lines.extend(["", "## Decisiones que aún requieren confirmación", ""])
    manual_decisions = plan.get("manual_decisions", [])
    if manual_decisions:
        lines.extend(
            f"{index}. {decision}"
            for index, decision in enumerate(manual_decisions, start=1)
        )
    else:
        lines.append("Ninguna.")
    lines.extend(
        [
            "",
            "## Guardas para una futura aplicación",
            "",
            "- Volver a leer Canvas inmediatamente antes de aplicar.",
            "- Asociar rúbricas aprobadas antes de publicar tareas.",
            "- Crear todos los objetos como no publicados.",
            "- Confirmar curso, fechas, puntos, grupos y modalidad con el docente.",
            "- Ejecutar de forma idempotente y verificar que no existan duplicados.",
            "- No publicar notas ni modificar entregas existentes.",
            "",
        ]
    )
    return "\n".join(lines)


def run_dry_run(args: argparse.Namespace, settings: Settings) -> None:
    course_id = require_course_id(settings)
    snapshot_path = Path(args.snapshot) if args.snapshot else settings.output_root / str(course_id) / "snapshot_latest.json"
    blueprint_path = Path(args.blueprint or DEFAULT_BLUEPRINT)
    snapshot = read_json_object(snapshot_path, "snapshot")
    blueprint = read_json_object(blueprint_path, "blueprint")
    plan = build_dry_run(snapshot, blueprint)
    output_dir = settings.output_root / str(course_id)
    json_path = output_dir / "dry_run_latest.json"
    markdown_path = output_dir / "dry_run_latest.md"
    write_json(json_path, plan)
    markdown_path.write_text(render_dry_run(snapshot, blueprint, plan), encoding="utf-8")
    print(f"Dry-run: {markdown_path.resolve()}")
    print("Canvas mutations: 0")
    print(
        f"Propuesta: {plan['proposed']['modules']} módulos, "
        f"{plan['proposed']['assignments']} actividades y "
        f"{plan['proposed']['assignment_groups']} grupos de evaluación."
    )


def run_doctor(client: CanvasReadOnlyClient, settings: Settings) -> None:
    course_id = require_course_id(settings)
    user = client.get_json("/api/v1/users/self")
    course = client.get_json(f"/api/v1/courses/{course_id}", params={"include[]": ["term"]})
    if not isinstance(user, dict) or not isinstance(course, dict):
        raise CanvasMVPError("No se pudo validar usuario y curso.")
    print("Conexión Canvas: OK")
    print(f"Usuario autenticado: {user.get('name')}")
    print(f"Curso: {course.get('id')} | {course.get('name')}")
    print(f"Estado: {course.get('workflow_state')}")
    print("TLS: verificación activa")
    print("Modo: solo lectura")


def run_list_courses(client: CanvasReadOnlyClient) -> None:
    courses = client.get_paginated(
        "/api/v1/courses",
        params={"enrollment_type": "teacher", "include[]": ["term"]},
    )
    for course in courses:
        term = course.get("term") or {}
        print(
            f"{course.get('id')} | {course.get('course_code')} | {course.get('name')} | "
            f"{course.get('workflow_state')} | {term.get('name', '')}"
        )


def run_snapshot(client: CanvasReadOnlyClient, settings: Settings, with_audit: bool) -> None:
    course_id = require_course_id(settings)
    snapshot = collect_snapshot(client, course_id)
    output_dir = settings.output_root / str(course_id)
    snapshot_path = output_dir / "snapshot_latest.json"
    write_json(snapshot_path, snapshot)
    print(f"Snapshot: {snapshot_path.resolve()}")
    if not with_audit:
        return
    audit = evaluate_snapshot(snapshot)
    audit_json_path = output_dir / "audit_latest.json"
    audit_md_path = output_dir / "audit_latest.md"
    write_json(audit_json_path, audit)
    audit_md_path.write_text(render_report(snapshot, audit), encoding="utf-8")
    print(f"Informe: {audit_md_path.resolve()}")
    print(f"Resultado: {audit['overall']}")
    print(f"Bloqueantes no cumplidos: {audit['summary']['blockers_failed']}")
    print(f"Bloqueantes por revisar: {audit['summary']['blockers_pending_review']}")


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--base-url")
    parser.add_argument("--course-id", type=int)
    parser.add_argument("--output-root")
    parser.add_argument("--keyring-service")
    parser.add_argument("--keyring-account")
    parser.add_argument(
        "--token-file",
        help="Compatibilidad transitoria. Preferir CANVAS_API_TOKEN o keyring.",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="MVP portable de diagnóstico, snapshot y dry-run para cursos MDS en Canvas."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command, help_text in [
        ("doctor", "Validar token, TLS y acceso al curso."),
        ("list-courses", "Listar cursos donde el usuario es docente."),
        ("snapshot", "Descargar solo estructura sin PII."),
        ("audit", "Crear snapshot e informe QA provisional."),
        ("dry-run", "Comparar el curso con el blueprint sin modificar Canvas."),
    ]:
        subparser = subparsers.add_parser(command, help=help_text)
        add_common_arguments(subparser)
        if command == "dry-run":
            subparser.add_argument("--blueprint")
            subparser.add_argument("--snapshot")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        settings = resolve_settings(args)
        if args.command == "dry-run":
            run_dry_run(args, settings)
            return 0
        token = resolve_token(args, settings)
        client = CanvasReadOnlyClient(settings.base_url, token)
        if args.command == "doctor":
            run_doctor(client, settings)
        elif args.command == "list-courses":
            run_list_courses(client)
        elif args.command == "snapshot":
            run_snapshot(client, settings, with_audit=False)
        elif args.command == "audit":
            run_snapshot(client, settings, with_audit=True)
        return 0
    except (CanvasMVPError, PermissionError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
