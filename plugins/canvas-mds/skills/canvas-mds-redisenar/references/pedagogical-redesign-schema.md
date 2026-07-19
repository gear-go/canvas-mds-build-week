# Contrato de rediseño pedagógico

Usar este contrato para producir `pedagogical-redesign.json`. El artefacto registra conclusiones auditables, no la cadena de pensamiento interna del modelo.

## Campos obligatorios

- `schema_version`: versión del contrato.
- `redesign_id`: identificador portable.
- `language`: idioma de los artefactos del curso.
- `source_evidence`: fuentes con `id`, `path`, `role` y `authority`; en contexto UDD incluir la base institucional empaquetada como fuente documentada.
- `current_assessment`: grupos, ponderaciones y descripción de qué evidencia observa hoy.
- `diagnosis`: problema de validez, procesos invisibles, riesgos asociados a IA y referencias de evidencia.
- `faculty_questions`: máximo tres preguntas; cada una declara estado, respuesta y referencias.
- `faculty_decisions`: decisiones confirmadas, modificadas o rechazadas con fundamento.
- `redesign_options`: al menos dos alternativas, exactamente una seleccionada.
- `selected_design`: checkpoints, evidencia individual, feedback, evidencia de uso de IA y `knowledge_base_refs` que fundamenten el diseño.
- `adversarial_scenarios`: escenarios, riesgo detectado, mitigación y actividades afectadas.
- `unresolved_decisions`: vacía antes de compilar el perfil final.

Desde `schema_version: 0.3.*` también es obligatorio `planning_alignment`: snapshot confirmado conforme a [planning-alignment-schema.md](planning-alignment-schema.md). Las versiones 0.2 se mantienen compatibles para conservar artefactos previos.

## Trazabilidad

Usar IDs únicos con prefijos `SRC-`, `Q-`, `FD-`, `OPT-` y `ADV-`. Cada hallazgo, opción y actividad propuesta debe referenciar fuentes o decisiones existentes.

Distinguir siempre:

- `documented`: proviene de una fuente;
- `faculty_confirmed`: proviene de una respuesta o decisión docente;
- `model_proposal`: propuesta de GPT-5.6 pendiente de aprobación.

No inventar fechas, pesos, políticas, resultados de aprendizaje ni capacidades de Canvas. Antes de validar el artefacto final, declarar una raíz portable y comprobar que el perfil y todas las rutas de `source_evidence` existan dentro de ella.

Para cursos UDD, usar referencias `UDD-R1`–`UDD-R10` y `UDD-H1`–`UDD-H6` según [metodologias-activas-udd.md](metodologias-activas-udd.md). Las reglas operativas pueden convertirse en controles determinísticos; las heurísticas requieren interpretación de GPT-5.6 y confirmación docente.

## Criterios de calidad

El diagnóstico debe preceder a la solución. Las preguntas deben poder cambiar el diseño. Las alternativas deben mostrar carga docente y trade-offs. La simulación adversarial debe examinar al menos producto generado con IA sin comprensión y contribución grupal desigual.

Antes de calendarizar, la versión 0.3 debe demostrar la cadena necesidad → objetivo → indicador → evidencia → instrumento → procedimiento. El objetivo no puede describir actividades; cada componente debe estar cubierto; la carga de revisión debe estar calculada; y el feedback debe tener uso posterior. Ningún artefacto final puede conservar `alignment_status: pending`.

La salida no puede calificar estudiantes ni afirmar autoría individual. Su función es rediseñar qué evidencia se solicitará en el futuro.
