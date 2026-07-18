---
name: canvas-mds-redisenar
description: Diagnostica y rediseña evaluaciones para hacer visible el proceso de aprendizaje en educación con IA. Usar cuando un docente necesite analizar qué demuestra una evaluación actual, identificar razonamiento, decisiones, iteración, feedback, contribución individual o uso responsable de IA que permanecen invisibles, comparar alternativas con trade-offs, resolver decisiones docentes y producir un perfil Canvas MDS trazable antes del dry-run.
---

# Canvas MDS · Rediseñar

Convertir evidencia del curso y decisiones docentes en un diseño de evaluación centrado en el proceso. No modificar Canvas desde este skill.

## Contrato

1. Leer [references/pedagogical-redesign-schema.md](references/pedagogical-redesign-schema.md) y [references/profile-schema.md](references/profile-schema.md) antes de generar artefactos.
2. En contexto UDD, consultar [references/metodologias-activas-udd.md](references/metodologias-activas-udd.md), especialmente las secciones 2, 4, 5, 9 y 11. Usar sus reglas `R1`–`R10` y heurísticas `H1`–`H6` como criterios trazables, no como una receta única.
3. Tratar programa y resultados aprobados como autoridad; usar planificación, rúbricas, políticas de IA y restricciones docentes como evidencia contextual.
4. Separar hechos documentados, respuestas docentes e inferencias de GPT-5.6. Asignar IDs estables y citar las fuentes en cada recomendación.
5. No mostrar cadena de pensamiento interna. Entregar diagnósticos y justificaciones breves, auditables y vinculadas a evidencia.
6. Preguntar antes de asumir una decisión pedagógica material. Mantener lo no resuelto en `manual_decisions`.
7. No calificar estudiantes, leer datos estudiantiles ni publicar o modificar Canvas.

## Flujo

### 1. Inventariar evidencia

Localizar programa, resultados de aprendizaje, evaluación y rúbrica actuales, planificación, guía institucional de IA y restricciones docentes. Registrar rutas relativas y crear `source_evidence` con IDs únicos.

### 2. Diagnosticar validez

Comparar lo que el curso declara, lo que practica y lo que realmente observa la evaluación. Identificar:

- dependencia del producto final;
- razonamiento, decisiones, iteración y feedback invisibles;
- contribución individual no verificable;
- usos de IA que permiten un buen producto sin demostrar aprendizaje;
- contradicciones y datos faltantes;
- alineamiento entre RA, actividades, evidencia y demanda cognitiva;
- oportunidades para autoevaluación, coevaluación, feedback utilizable y formatos alternativos de evidencia.

Vincular cada hallazgo con evidencia. En cursos UDD, citar los identificadores `UDD-R*` o `UDD-H*` pertinentes. No proponer cambios todavía.

### 3. Preguntar

Formular como máximo tres preguntas docentes de alto valor. Priorizar qué debe defender cada estudiante, si se valora corrección inicial o mejora, qué uso de IA se permite y cuánta carga de revisión es viable. Esperar respuesta cuando cambie sustancialmente el diseño.

### 4. Proponer alternativas

Generar al menos dos opciones: una ligera y otra de mayor verificación. Para cada opción explicar beneficios, riesgos, carga docente y trade-offs. Conservar el producto auténtico, pero rodearlo de checkpoints que hagan visible el aprendizaje. Elegir metodologías activas por su coherencia con los RA, el contexto, la diversidad del grupo y la viabilidad docente; no por popularidad ni por coincidencia de palabras.

### 5. Simular fallas de validez

Probar el diseño contra escenarios de producto generado con IA sin comprensión, trabajo grupal desigual, buen proceso con producto imperfecto y uso de IA declarado pero no verificado. Proponer mitigaciones concretas sin convertir la IA en calificadora.

### 6. Confirmar decisiones

Registrar selección, modificaciones y rechazos como `faculty_decisions`. Exigir estado `confirmed` para toda decisión que llegue al perfil. Mantener preguntas no respondidas en `manual_decisions`.

### 7. Entregar artefactos

Crear en `canvas_profiles/<slug>/`:

- `pedagogical-redesign.json` desde [assets/pedagogical-redesign-template.json](assets/pedagogical-redesign-template.json);
- `course-profile.json` desde [assets/course-profile-template.json](assets/course-profile-template.json);
- `before-after.md` con el cambio de evidencia de producto a proceso.

El perfil debe incorporar un snapshot aprobado de `pedagogical_redesign`, referencias a fuentes y decisiones, `process_assessment_policy` y metadatos de proceso por actividad. En contexto UDD debe registrar `knowledge_base_refs`, procesos cognitivos, dimensiones del conocimiento, actor del feedback y formatos alternativos de evidencia.

### 8. Validar y transferir

Ejecutar la validación determinística antes de recomendar `$canvas-mds-gestionar`. Resumir qué comprendió GPT-5.6, qué decidió el docente, qué reglas verificó el motor y qué sigue pendiente. Nunca ejecutar escritura desde este skill.

## Portabilidad

No incluir URL, ID o token de Canvas, nombres de estudiantes, entregas, notas ni reportes locales. Usar evidencia de curso sanitizada y rutas relativas. Las decisiones comunes pertenecen al plugin; las decisiones del curso permanecen en sus artefactos.
