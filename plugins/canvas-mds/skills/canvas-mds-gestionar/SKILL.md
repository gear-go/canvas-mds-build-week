---
name: canvas-mds-gestionar
description: Inspecciona, audita y crea de forma controlada mediante el adaptador Canvas MDS de AssessTrace a partir de un perfil aprobado. Usar para snapshot, dry-run, revisión de módulos y evaluaciones, diagnóstico de preparación, creación explícita como no publicada o resolución de dudas sobre el siguiente paso.
---

# AssessTrace · Gestionar con el adaptador Canvas MDS

Opera Canvas con lectura por defecto y una única ruta de escritura acotada, idempotente y no publicada.

## Antes de operar

1. Confirmar que `$canvas-mds-configurar` terminó correctamente.
2. Leer [references/commands.md](references/commands.md) y [references/readiness.md](references/readiness.md).
3. Localizar el perfil aprobado y validar que `manual_decisions` esté vacío.
4. No usar este MVP para estudiantes, matrículas, entregas, notas, comentarios, publicación o eliminación.

## Seleccionar operación

- Pregunta de estado o estructura: ejecutar snapshot y, si corresponde, auditoría.
- Propuesta de cambios: ejecutar siempre dry-run.
- Solicitud ambigua como "subir" o "crear": mostrar dry-run y pedir aprobación específica; no escribir todavía.
- Solicitud explícita "crear en el curso N como no publicado": verificar identidad, confirmar el mismo ID y ejecutar la ruta protegida.
- Solicitud de publicar: detenerse; está fuera del MVP y requiere revisión docente, rúbricas y Vista del estudiante.

## Lectura

Usar `scripts/canvas_mds.py` para `doctor`, `list-courses`, `snapshot`, `audit` y `dry-run`. Mantener los reportes bajo `.canvas/reports/<course_id>/`; no compartirlos automáticamente.

El dry-run debe comparar por nombre los grupos, actividades, páginas y módulos, mostrar qué se crearía y declarar `canvas_mutations: 0`.

## Escritura protegida

Solo con autorización explícita ejecutar:

`python <plugin>/scripts/canvas_mds_apply.py --blueprint <perfil> --confirm-course-id <id> --confirm-unpublished`

Antes de llamar al comando, repetir al docente nombre/código e ID del curso. El motor debe:

- exigir `default_publish=false` y cero decisiones pendientes;
- validar identidad y ponderación;
- crear o reutilizar por nombre;
- abortar ante un objetivo ya publicado o incompatible;
- usar solo POST/PUT y no reintentar mutaciones automáticamente;
- verificar al final que todos los objetivos siguen no publicados.

## Auditoría y dudas de avance

Clasificar hallazgos en: automático, revisión docente o sin permiso. Informar primero bloqueantes y tres acciones prioritarias. Las páginas de plantilla, rúbricas ausentes, enlaces/accesibilidad y Vista del estudiante mantienen el estado `NO_LISTO_PROVISIONAL` aunque la estructura exista.

Cuando el docente pregunte "¿cómo seguimos?", responder desde el último reporte y el perfil: decisión pendiente, corrección de perfil, nuevo dry-run, aplicación no publicada o revisión docente. No repetir escrituras si una lectura basta.

## Evidencia de cierre

Entregar rutas de snapshot, dry-run, informe de aplicación y auditoría; incluir conteos creados/reutilizados y confirmar visibilidad. Nunca incluir secretos o datos de estudiantes.
