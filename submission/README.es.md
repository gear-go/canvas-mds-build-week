# Envío de AssessTrace como paquete de skills

[English version](README.md)

Este directorio contiene los materiales legibles por personas para presentar **AssessTrace · Canvas MDS** como un plugin compuesto únicamente por skills.

## Paquete

El artefacto que debe cargarse es:

`dist/assesstrace-canvas-mds-skills-only-0.1.0.zip`

El ZIP contiene una sola raíz de plugin con:

- `.codex-plugin/plugin.json`
- `skills/`
- `scripts/`
- `assets/`

El paquete excluye deliberadamente el marketplace del repositorio, configuración local, credenciales Canvas, reportes, documentación para jueces y perfiles de ejemplo ubicados fuera de la raíz del plugin.

## Tipo de envío

Seleccionar **Skills only** en el portal de envío de plugins de OpenAI.

## Materiales

- [listing.es.md](listing.es.md): ficha pública propuesta, datos de publicación, prompts iniciales y bloqueos pendientes.
- [test-cases.es.md](test-cases.es.md): cinco casos positivos y tres casos negativos para revisión.

## Condiciones pendientes antes del envío

1. Verificar la identidad del publicador que se mostrará públicamente. Si la universidad será el publicador, se debe utilizar una identidad institucional aprobada por UDD.
2. Obtener permiso de escritura para Apps Management en la organización de OpenAI Platform que realizará el envío.
3. Publicar y aprobar las URLs definitivas del sitio, soporte, política de privacidad y términos de servicio.
4. Confirmar los países o regiones donde el soporte y los términos legales se encuentran disponibles.
5. Revisar y aprobar las notas de versión y declaraciones de cumplimiento dentro del portal.

El paquete no contiene tokens, credenciales, registros estudiantiles, matrículas, entregas ni calificaciones.
