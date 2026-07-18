# Comandos del motor Canvas MDS

Ejecutar desde la carpeta del curso. Reemplazar `<plugin>` por la ruta absoluta a `plugins/canvas-mds` y `<perfil>` por el perfil aprobado.

## Lectura y diagnóstico

- `python <plugin>/scripts/canvas_mds.py doctor`
- `python <plugin>/scripts/canvas_mds.py list-courses`
- `python <plugin>/scripts/canvas_mds.py snapshot`
- `python <plugin>/scripts/canvas_mds.py audit`
- `python <plugin>/scripts/canvas_mds.py dry-run --blueprint <perfil>`

Los resultados se guardan en `.canvas/reports/<course_id>/`.

## Escritura controlada

Solo después de revisar el dry-run y recibir autorización explícita para el curso correcto:

`python <plugin>/scripts/canvas_mds_apply.py --blueprint <perfil> --confirm-course-id <id> --confirm-unpublished`

La operación usa POST/PUT, es reejecutable por nombre y se detiene ante objetos objetivo publicados, pesos incompatibles, identidad incorrecta o decisiones pendientes. No existe comando de publicación ni eliminación en este MVP.

