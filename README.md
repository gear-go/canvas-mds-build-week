# Canvas MDS portable · MVP 0.1.0

Paquete compartible para que docentes MDS trabajen con el mismo flujo en Codex y adapten cada curso mediante un perfil JSON. Incluye tres skills: conexión segura, adaptación pedagógica y gestión controlada de Canvas.

## Alcance del MVP

- Lee la estructura del curso y genera snapshots, auditorías y dry-runs.
- Crea grupos de evaluación, una categoría de equipos, páginas, tareas, un Classic Quiz y módulos.
- Toda creación queda **no publicada** y exige confirmar explícitamente el ID del curso.
- No publica, no elimina, no modifica matrículas, no descarga entregas y no escribe notas.
- El ejemplo de Entornos Digitales se incluye como referencia; cada docente debe generar y aprobar su propio perfil.

## Instalación para docentes

1. Descomprimir o clonar esta carpeta en el computador del docente.
2. Registrar el marketplace local: `codex plugin marketplace add <ruta-absoluta-a-canvas_mds_portable>`.
3. Instalar el plugin: `codex plugin install canvas-mds@canvas-mds-docentes`.
4. Reiniciar Codex y comenzar con `$canvas-mds-configurar`.

## Seguridad

El paquete no contiene tokens, IDs de cursos ni snapshots. El token se guarda en el keyring del sistema operativo o se entrega por la variable temporal `CANVAS_API_TOKEN`; nunca se pega en el chat ni se agrega al repositorio. La configuración local vive en `.canvas/local.json`, ruta ignorada por Git.

## Flujo recomendado

1. `$canvas-mds-configurar`: configura URL, ID y credencial local; ejecuta `doctor`.
2. `$canvas-mds-adaptar`: convierte programa, planificación y decisiones del docente en un perfil revisable.
3. `$canvas-mds-gestionar`: obtiene snapshot, hace dry-run y audita.
4. Solo con aprobación explícita: crea la estructura como no publicada y verifica el resultado.

Las instrucciones detalladas están dentro de cada skill. El motor compartido está en `plugins/canvas-mds/scripts/` y los perfiles de ejemplo en `plugins/canvas-mds/assets/profiles/`.

