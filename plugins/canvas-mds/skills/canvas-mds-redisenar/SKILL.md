---
name: canvas-mds-redisenar
description: Aplica la metodología Evidence by Design de AssessTrace para diagnosticar y rediseñar evaluaciones, cursos y jornadas que hagan visible el proceso de aprendizaje con IA. Usar cuando un docente necesite alinear necesidad, objetivos, indicadores, evidencias, instrumentos, procedimientos y actividades; identificar razonamiento, decisiones, iteración, feedback, contribución individual o uso responsable de IA invisibles; comparar alternativas y producir un perfil Canvas MDS trazable antes del dry-run.
---

# AssessTrace · Evidence by Design

Aplicar Evidence by Design para convertir evidencia y decisiones docentes en un diseño cuyo proceso de aprendizaje sea visible y trazable. El docente decide; AssessTrace registra y valida. No modificar Canvas desde este skill.

## Contrato

1. Leer [references/pedagogical-redesign-schema.md](references/pedagogical-redesign-schema.md), [references/profile-schema.md](references/profile-schema.md), [references/planning-alignment.md](references/planning-alignment.md) y [references/planning-alignment-schema.md](references/planning-alignment-schema.md) antes de generar artefactos.
2. En contexto UDD, consultar [references/metodologias-activas-udd.md](references/metodologias-activas-udd.md), especialmente las secciones 2, 4, 5, 9 y 11. Usar reglas `R1`–`R10` y heurísticas `H1`–`H6` como criterios trazables, no como receta.
3. Tratar programa y resultados aprobados como autoridad. No reescribir objetivos aprobados silenciosamente. Usar planificación, rúbricas, políticas de IA y restricciones como evidencia contextual.
4. Distinguir siempre necesidad, objetivo, actividad, indicador, evidencia, instrumento y procedimiento. Un objetivo describe qué podrá demostrar la persona; una actividad, qué hará durante la experiencia.
5. Separar hechos documentados, respuestas docentes e inferencias de GPT-5.6. Asignar IDs estables y citar fuentes en cada recomendación.
6. No mostrar cadena de pensamiento interna. Entregar diagnósticos y justificaciones breves, auditables y vinculadas a evidencia.
7. Preguntar antes de asumir una decisión pedagógica material. Si queda una pregunta material sin responder, aplicar `HARD STOP 1`. Mantener lo no resuelto en `manual_decisions`.
8. No cambiar ponderaciones, modalidad, carga docente, formato individual ni una restricción documentada sin confirmación explícita.
9. No calificar estudiantes, leer datos estudiantiles ni publicar o modificar Canvas.
10. Seleccionar todo instrumento usado por el procedimiento. Mantener `selected: false` solo para alternativas comparadas y descartadas.
11. Trazar cada fila de la matriz a exactamente un objetivo y un componente; prohibir relaciones cartesianas o referencias espurias. Cuando un objetivo tenga varios indicadores, sus tres componentes no pueden repetir una firma downstream idéntica.

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

No volver a preguntar aquello que una fuente autorizada ya responde. Formular como máximo tres preguntas únicamente sobre brechas que puedan cambiar ponderaciones, modalidad, evidencia individual, uso de IA, accesibilidad o carga docente. Antes de recomendar una revisión individual, calcular su carga total con el tamaño de la cohorte; distinguir tiempo del estudiante y tiempo de revisión docente.

**Puerta obligatoria · HARD STOP 1:** si al menos una pregunta material queda sin responder, terminar el turno inmediatamente después de enumerarla. En ese turno:

- entregar solo inventario breve, diagnóstico y preguntas;
- no proponer alternativas, ponderaciones ni recomendaciones provisionales;
- no simular escenarios adversariales;
- no crear ni modificar archivos o perfiles;
- no ejecutar los pasos 4–9.

Reanudar el paso 4 únicamente después de recibir respuestas explícitas. No convertir supuestos en decisiones docentes. Una solicitud como «primero diagnostica y pregunta» activa siempre esta puerta.

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
- comparar al menos tres instrumentos, seleccionar uno principal y calcular por separado carga docente y carga de estudiantes o pares;
- declarar momentos diagnósticos, de seguimiento y finales cuando sean pertinentes;
- exigir feedback con uso posterior;
- construir la matriz objetivo → indicador → evidencia → instrumento → momento con una fila por objetivo y componente, sin ampliar relaciones;
- validar `planning-alignment.json` antes de diseñar actividades.

### 5. Proponer alternativas de rediseño

Generar al menos dos opciones: una ligera y otra de mayor verificación. Para cada una explicar beneficios, riesgos, carga y trade-offs. Conservar el producto auténtico y toda restricción confirmada, rodeándolo de checkpoints que hagan visible el aprendizaje. Mostrar el cálculo de carga cuando dependa del tamaño de la cohorte. Elegir metodologías por coherencia con objetivos, contexto, diversidad y viabilidad.

Solicitar que el docente seleccione, modifique o rechace las opciones.

**Puerta obligatoria · HARD STOP 2:** mientras no exista una selección explícita, no marcar una opción como elegida, no construir `selected_design`, no ejecutar la simulación final y no generar artefactos. Terminar el turno después de solicitar la decisión.

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

Antes de escribir, declarar una única raíz portable que contenga las fuentes y la carpeta `canvas_profiles`. Crear los artefactos dentro de esa raíz y comprobar que cada `source_evidence.path` resuelva desde ella; nunca crear una carpeta hermana fuera de la raíz asumida. En perfiles 0.3, cada actividad debe referenciar una cadena existente mediante `objective_ids`, `indicator_ids`, `evidence_ids`, `instrument_id` y `procedure_moment_id`.

En `before-after.md`, separar categorías excluyentes —producto final, checkpoints de proceso y verificación individual— y declarar aparte el total de evidencia no final. No usar la misma etiqueta para el subtotal y el total.

### 9. Validar y transferir

Ejecutar la validación determinística desde la raíz portable antes de recomendar `$canvas-mds-gestionar`:

```powershell
python plugins/canvas-mds/scripts/process_evidence.py --profile canvas_profiles/<slug>/course-profile.json --repository-root .
```

Resumir qué comprendió GPT-5.6, qué decidió el docente, qué reglas verificó el motor y qué sigue pendiente. Nunca ejecutar escritura desde este skill.

## Portabilidad

No incluir URL, ID o token de Canvas, nombres de estudiantes, entregas, notas ni reportes locales. Usar evidencia sanitizada. Mostrar y almacenar rutas relativas a la raíz portable declarada; nunca emitir rutas absolutas del equipo local. Exigir que perfil y fuentes resuelvan dentro de esa raíz. Las decisiones comunes pertenecen al plugin; las decisiones del curso permanecen en sus artefactos.
