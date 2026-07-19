---
name: canvas-mds-redisenar
description: Diagnostica y rediseña evaluaciones, cursos y jornadas para hacer visible el proceso de aprendizaje en educación con IA. Usar cuando un docente necesite alinear necesidad, objetivos, indicadores, evidencias, instrumentos, procedimientos y actividades; identificar razonamiento, decisiones, iteración, feedback, contribución individual o uso responsable de IA invisibles; comparar alternativas y producir un perfil Canvas MDS trazable antes del dry-run.
---

# Canvas MDS · Rediseñar

Convertir evidencia y decisiones docentes en un diseño centrado en el proceso. No modificar Canvas desde este skill.

## Contrato

1. Leer [references/pedagogical-redesign-schema.md](references/pedagogical-redesign-schema.md), [references/profile-schema.md](references/profile-schema.md), [references/planning-alignment.md](references/planning-alignment.md) y [references/planning-alignment-schema.md](references/planning-alignment-schema.md) antes de generar artefactos.
2. En contexto UDD, consultar [references/metodologias-activas-udd.md](references/metodologias-activas-udd.md), especialmente las secciones 2, 4, 5, 9 y 11. Usar reglas `R1`–`R10` y heurísticas `H1`–`H6` como criterios trazables, no como receta.
3. Tratar programa y resultados aprobados como autoridad. No reescribir objetivos aprobados silenciosamente. Usar planificación, rúbricas, políticas de IA y restricciones como evidencia contextual.
4. Distinguir siempre necesidad, objetivo, actividad, indicador, evidencia, instrumento y procedimiento. Un objetivo describe qué podrá demostrar la persona; una actividad, qué hará durante la experiencia.
5. Separar hechos documentados, respuestas docentes e inferencias de GPT-5.6. Asignar IDs estables y citar fuentes en cada recomendación.
6. No mostrar cadena de pensamiento interna. Entregar diagnósticos y justificaciones breves, auditables y vinculadas a evidencia.
7. Preguntar antes de asumir una decisión pedagógica material. Mantener lo no resuelto en `manual_decisions`.
8. No calificar estudiantes, leer datos estudiantiles ni publicar o modificar Canvas.

## Flujo

### 1. Inventariar evidencia

Localizar programa, resultados de aprendizaje, evaluación y rúbrica actuales, planificación, guía de IA y restricciones docentes. Registrar rutas relativas y crear `source_evidence` con IDs únicos.

### 2. Diagnosticar validez

Comparar lo declarado, lo practicado y lo observado por la evaluación. Identificar:

- dependencia del producto final;
- razonamiento, decisiones, iteración y feedback invisibles;
- contribución individual no verificable;
- uso de IA que permite buen producto sin demostrar aprendizaje;
- contradicciones, datos faltantes y carga docente;
- alineamiento entre RA, evidencia y demanda cognitiva;
- oportunidades para autoevaluación, coevaluación, feedback utilizable y formatos equivalentes.

Vincular cada hallazgo con evidencia y, en UDD, con identificadores `UDD-R*` o `UDD-H*`. No proponer cambios todavía.

### 3. Resolver preguntas docentes

Formular como máximo tres preguntas de alto valor. Priorizar qué debe demostrar cada participante, si se valora corrección inicial o mejora, uso permitido de IA y carga de revisión viable.

**HARD STOP 1:** si una respuesta puede cambiar materialmente el diseño, detenerse después de las preguntas. No proponer alternativas, porcentajes, agenda, actividades, archivos ni perfil hasta recibir respuesta explícita. No convertir supuestos en decisiones docentes.

### 4. Alinear antes de calendarizar

Preservar los resultados aprobados. Si están documentados, descomponerlos sin alterar su autoridad. Si falta un objetivo o el docente pide revisarlo:

1. proponer dos o tres alternativas de una oración;
2. separar acción observable, contenido o desempeño y condición;
3. comprobar viabilidad dentro de la duración;
4. excluir actividades, recursos, secuencias e instrumentos;
5. explicar diferencias y trade-offs.

**ALIGNMENT STOP:** hasta que el docente confirme explícitamente un objetivo nuevo o revisado, no derivar indicadores, evidencia, instrumentos, procedimiento, agenda, módulos, actividades ni archivos.

Después de la confirmación:

- derivar entre cuatro y seis indicadores observables de proceso y resultado;
- vincular cada indicador con evidencia concreta y cubrir acción, contenido y condición;
- comparar al menos tres instrumentos, seleccionar uno principal y calcular carga real;
- declarar momentos diagnósticos, de seguimiento y finales cuando sean pertinentes;
- exigir feedback con uso posterior;
- construir la matriz objetivo → indicador → evidencia → instrumento → momento;
- validar `planning-alignment.json` antes de diseñar actividades.

### 5. Proponer alternativas de rediseño

Generar al menos dos opciones: una ligera y otra de mayor verificación. Para cada una explicar beneficios, riesgos, carga y trade-offs. Conservar el producto auténtico, rodeándolo de checkpoints que hagan visible el aprendizaje. Elegir metodologías por coherencia con objetivos, contexto, diversidad y viabilidad.

**HARD STOP 2:** presentar las alternativas y pedir una selección o modificación explícita. No crear artefactos finales, perfil ni recomendar gestión de Canvas mientras ninguna alternativa esté seleccionada.

### 6. Simular fallas de validez

Probar contra producto generado con IA sin comprensión, trabajo grupal desigual, buen proceso con producto imperfecto y uso de IA declarado pero no verificado. Proponer mitigaciones sin convertir la IA en calificadora.

### 7. Confirmar decisiones

Registrar selecciones, modificaciones y rechazos como `faculty_decisions`. Exigir estado `confirmed` para toda decisión que llegue al perfil. Mantener preguntas no respondidas en `manual_decisions`.

### 8. Entregar artefactos

Solo después de superar los tres stops, crear en `canvas_profiles/<slug>/`:

- `planning-alignment.json` desde [assets/planning-alignment-template.json](assets/planning-alignment-template.json);
- `pedagogical-redesign.json` desde [assets/pedagogical-redesign-template.json](assets/pedagogical-redesign-template.json);
- `course-profile.json` desde [assets/course-profile-template.json](assets/course-profile-template.json);
- `before-after.md` con el cambio de evidencia de producto a proceso.

El perfil incorpora snapshots aprobados, fuentes, decisiones, `process_assessment_policy` y metadatos de proceso por actividad. En UDD registra `knowledge_base_refs`, procesos cognitivos, dimensiones del conocimiento, actor del feedback y formatos equivalentes.

### 9. Validar y transferir

Ejecutar la validación determinística antes de recomendar `$canvas-mds-gestionar`. Resumir qué comprendió GPT-5.6, qué decidió el docente, qué reglas verificó el motor y qué sigue pendiente. Nunca ejecutar escritura desde este skill.

## Portabilidad

No incluir URL, ID o token de Canvas, nombres de estudiantes, entregas, notas ni reportes locales. Usar evidencia sanitizada y rutas relativas. Las decisiones comunes pertenecen al plugin; las decisiones del curso permanecen en sus artefactos.
