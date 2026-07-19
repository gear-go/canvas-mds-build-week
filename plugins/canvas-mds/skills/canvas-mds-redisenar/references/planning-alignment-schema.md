# Contrato de planning-alignment.json

El artefacto registra decisiones confirmadas y una cadena auditable; no contiene razonamiento interno.

## Campos

- `schema_version`, `alignment_id`, `alignment_status`.
- `scope`: `course`, `unit`, `workshop`, `assessment` o `intervention`.
- `need`, `audience`, `duration.value` y `duration.unit`.
- `objectives`: id, statement, observable_action, content_or_performance, condition, status, activity_free, source_evidence_ids y faculty_decision_ids cuando corresponda.
- `indicators`: id, statement, type (`process` o `result`), observable, attendance_or_participation_only, quality_condition, objective_ids y evidence_ids.
- `evidence`: id, description, scope e indicator_ids.
- `instruments`: al menos tres alternativas con type, role, selected, rationale, advantages, limitations y relaciones. Los seleccionados incluyen `review_workload`; `counts_toward_faculty_capacity=false` separa la carga de pares, estudiantes o externos.
- `evaluation_procedure.moments`: id, stage, actor, action, evidence_ids, instrument_ids, feedback y feedback_use.
- `alignment_matrix`: una fila por objetivo y por componente (`action`, `content_or_performance`, `condition`), con referencias directas y no espurias a toda la cadena.
- `unresolved_decisions`: vacío en un artefacto final.

`alignment_status` debe ser `confirmed` antes de diseñar actividades. Debe existir exactamente un instrumento principal. Todo instrumento usado por el procedimiento debe estar seleccionado y todo instrumento seleccionado debe usarse. Las relaciones indicador-evidencia son bidireccionales. La carga estimada debe coincidir con elementos × minutos y declarar si consume capacidad docente.

Cada fila de la matriz contiene exactamente un `objective_id`. Sus indicadores deben referenciar ese objetivo; sus evidencias, esos indicadores; sus instrumentos seleccionados, esas evidencias; y sus momentos, esos instrumentos y evidencias. La unión de filas debe cubrir todos los elementos sin crear una matriz cartesiana artificial.

Validar con `scripts/planning_alignment.py`.
