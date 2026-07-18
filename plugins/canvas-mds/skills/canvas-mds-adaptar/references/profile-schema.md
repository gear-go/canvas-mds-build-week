# Perfil de curso Canvas MDS

El perfil JSON es la fuente de verdad para el motor portable. No debe contener IDs de Canvas ni credenciales.

## Campos obligatorios

- `version`, `course_profile`, `timezone`, `default_publish=false`.
- `course_identity.required_terms`: términos distintivos del nombre o código Canvas.
- `source_files`: programa, planificación, guía y documentos usados.
- `assignment_groups`: nombres y pesos que sumen 100.
- `assignments`: clave única, nombre, puntos, fecha local, modalidad, RA, evidencia y grupo.
- `modules`: nombre, posición, páginas y claves de actividades.
- `course_policies`: decisiones confirmadas y su fundamento.
- `manual_decisions`: vacía antes de autorizar cualquier escritura.

## Convenciones del MVP

- Exactamente un Classic Quiz, identificado por `quiz_settings`.
- Cada pregunta declara `name`, `points`, `type` y `prompt`; sus puntos suman los puntos del quiz.
- Una tarea de equipo declara `group_assignment=true` y requiere `team_group_category`.
- Para actividades sin entrega digital, usar `submission_types: ["on_paper"]`.
- `due_local` y `unlock_local` usan `YYYY-MM-DD HH:MM` en la zona horaria del perfil.
- Los `components` de un grupo, si existen, suman su peso y coinciden con `course_weight_percent` de las actividades.

## Puertas de aprobación

Mantener una decisión en `manual_decisions` cuando falte fecha, incidencia, rúbrica, modalidad, política de atraso, uso de IA/datos o aprobación del programa. El motor se negará a escribir mientras la lista no esté vacía.

