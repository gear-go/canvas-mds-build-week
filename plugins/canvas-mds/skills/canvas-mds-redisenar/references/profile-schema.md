# Perfil de curso Canvas MDS

El perfil JSON es la fuente portable para el motor determinístico. No debe contener IDs de Canvas, credenciales ni datos de estudiantes.

## Campos base obligatorios

- `version`, `course_profile`, `timezone`, `default_publish=false`.
- `course_identity.required_terms`: términos distintivos del curso.
- `source_files`: documentos utilizados.
- `assignment_groups`: nombres y pesos que suman 100.
- `assignments`: clave única, nombre, puntos, fecha, modalidad, RA, evidencia y grupo.
- `modules`: nombre, posición, páginas y claves de actividades.
- `course_policies`: decisiones confirmadas y fundamento.
- `manual_decisions`: vacía antes de autorizar escritura.

## Rediseño centrado en el proceso

Cuando `process_assessment_policy.enabled=true`, incluir:

- `pedagogical_redesign`: snapshot aprobado conforme a [pedagogical-redesign-schema.md](pedagogical-redesign-schema.md);
- `pedagogical_redesign.planning_alignment`: cadena confirmada de objetivo, indicadores, evidencias, instrumentos y procedimiento para perfiles 0.3;
- `process_assessment_policy.minimum_process_weight_percent`;
- `require_individual_evidence_for_group_work`;
- `require_feedback_iteration`;
- `require_ai_use_disclosure`;
- `require_self_or_peer_assessment`;
- `require_alternative_evidence_formats`;
- `knowledge_base_refs`: reglas y heurísticas institucionales aplicadas, por ejemplo `UDD-R1` y `UDD-H3`.

Cada actividad debe declarar:

- `course_weight_percent`, incluyendo cero para evidencia formativa;
- `process_stage`;
- `evidence_scope`: `individual`, `team` o `mixed`;
- `process_dimensions`, incluyendo `self_assessment` o `peer_assessment` en al menos una actividad cuando la política lo exija;
- `cognitive_processes` y `knowledge_dimensions` para hacer explícita la demanda cognitiva;
- `alternative_evidence_formats`, con al menos una vía equivalente y accesible;
- `knowledge_base_refs` cuando la decisión derive de una regla o heurística institucional;
- `ai_use.level`, `disclosure_required` y `verification_required`;
- `source_evidence_ids`;
- `faculty_decision_ids`;
- `feedback_loop.receives_feedback`, `requires_response`, `actor` cuando corresponda y `response_in_assignment_key` cuando el estudiante deba usar el feedback en una entrega posterior.

En perfiles generados desde un rediseño 0.3, cada actividad también declara `objective_ids`, `indicator_ids`, `evidence_ids`, `instrument_id` y `procedure_moment_id`. Estas referencias deben existir en `planning_alignment`; una actividad no puede ampliar silenciosamente el objetivo.

El perfil final se valida desde una raíz portable explícita. El archivo debe estar dentro de esa raíz y cada ruta de `source_files` o `source_evidence.path` debe resolver dentro de ella. Ser relativa no basta si la ruta solo funciona desde otra carpeta asumida.

El peso de proceso corresponde a actividades cuyo `process_stage` no sea `final_product`.

## Convenciones del MVP

- Exactamente un Classic Quiz, identificado por `quiz_settings`.
- Las preguntas del quiz tienen nombre único y sus puntos suman el total.
- Una tarea de equipo declara `group_assignment=true` cuando Canvas debe configurarla como grupal.
- Para actividades sin entrega digital usar `submission_types: ["on_paper"]`.
- `due_local` y `unlock_local` usan `YYYY-MM-DD HH:MM`.
- Los componentes de cada grupo, si existen, suman el peso del grupo y coinciden con `course_weight_percent`.

## Puertas de aprobación

Mantener una decisión en `manual_decisions` cuando falte fecha, incidencia, rúbrica, modalidad, política de atraso, uso de IA/datos o aprobación del diseño. El motor se negará a escribir mientras exista una decisión pendiente.

También detener la generación cuando falte confirmar un objetivo nuevo o revisado, o cuando la cadena de alineamiento no supere su validación determinística.

Validar el bundle final con `python plugins/canvas-mds/scripts/process_evidence.py --profile canvas_profiles/<slug>/course-profile.json --repository-root .` ejecutado desde la raíz portable.
