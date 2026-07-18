# Canvas MDS · Diseño de cursos centrado en el proceso con IA

> Un complemento seguro para Codex que convierte documentos de curso, lineamientos institucionales de IA y decisiones docentes en blueprints revisables para Canvas LMS.

[English version](README.md)

Canvas MDS ayuda a diseñar y construir cursos alrededor del **proceso de aprendizaje**, no solo del producto final. Combina la capacidad interpretativa de **Codex con GPT-5.6** con un motor Python determinista que inspecciona Canvas, produce dry-runs sin mutaciones y solo puede crear estructuras no publicadas que hayan sido aprobadas explícitamente.

El MVP fue diseñado para docentes del ecosistema de la Maestría en Data Science (MDS) de la Universidad del Desarrollo (UDD), pero su arquitectura basada en perfiles puede adaptarse a otros cursos e instituciones.

## El problema

La IA generativa cambia lo que una entrega final permite demostrar. Los docentes necesitan una manera práctica de rediseñar actividades, checkpoints, evidencia individual, políticas de uso de IA y secuencias de evaluación sin reconstruir manualmente cada curso en Canvas ni delegar las decisiones pedagógicas a un sistema automatizado.

Canvas MDS separa:

- los lineamientos compartidos a nivel institucional y de programa;
- la evidencia extraída del programa aprobado y la planificación;
- las decisiones que todavía requieren al docente;
- las operaciones deterministas de Canvas que pueden revisarse antes de ejecutarse.

## Qué hace el MVP

- Lee la estructura del curso sin recuperar entregas, notas ni matrículas.
- Produce snapshots estructurales, auditorías provisionales y dry-runs sin mutaciones.
- Convierte documentos del curso y decisiones confirmadas en un perfil JSON portable.
- Crea o reutiliza grupos de evaluación, una categoría de equipos, páginas, tareas, un Classic Quiz y módulos.
- Exige confirmar el ID exacto del curso Canvas antes de cualquier escritura.
- Crea todo como **no publicado** y verifica ese estado después de ejecutar.
- Se niega a escribir cuando existen decisiones pendientes, pesos incompatibles, identidad incorrecta o un objeto objetivo ya publicado.

Deliberadamente **no** publica ni elimina contenido, modifica matrículas, descarga entregas, publica comentarios ni escribe notas.

## Cómo funciona

| Capa | Responsabilidad |
| --- | --- |
| Evidencia del curso | Programa aprobado, planificación, lineamientos institucionales y decisiones explícitas del docente. |
| Codex + GPT-5.6 | Interpreta documentos, detecta contradicciones y decisiones faltantes, ayuda a crear un perfil trazable y orquesta las tres skills. |
| Perfil JSON | Guarda resultados de aprendizaje, ponderaciones, evidencia de proceso, fechas, políticas de IA/datos, páginas, módulos y decisiones pendientes sin credenciales ni IDs de Canvas. |
| Motor Python determinista | Valida invariantes, lee la estructura de Canvas, calcula el dry-run, aplica el plan autorizado y verifica el resultado. |
| API de Canvas LMS | Recibe lecturas por defecto y solicitudes POST/PUT protegidas solo después de una confirmación explícita. |

GPT-5.6 se utiliza dentro de Codex como capa de razonamiento y orquestación. El motor Python no realiza una llamada oculta a un modelo: su función es que las reglas de seguridad sean comprobables y predecibles.

## Las tres skills

| Skill | Propósito | Comportamiento de escritura |
| --- | --- | --- |
| **$canvas-mds-configurar** | Configura URL, ID del curso, reportes locales y fuente segura de credencial; luego diagnostica la conexión. | Solo configuración local. Nunca solicita el token en el chat. |
| **$canvas-mds-adaptar** | Convierte documentos y decisiones docentes en un perfil JSON revisable. | Escribe un perfil local; nunca modifica Canvas. |
| **$canvas-mds-gestionar** | Inspecciona, audita, hace dry-run y, solo tras una aprobación precisa, crea una estructura no publicada. | Lectura por defecto; la única escritura es una creación protegida, idempotente y no publicada. |

## Cómo se utilizaron Codex y GPT-5.6

Durante Build Week, Codex con GPT-5.6 aceleró el paso desde las necesidades educativas hasta un complemento funcional:

- tradujo restricciones docentes, de política de IA, privacidad y evaluación a una arquitectura de tres skills;
- ayudó a separar el juicio docente de las operaciones que podían automatizarse de forma segura;
- implementó e iteró los motores Python de lectura y escritura protegida;
- generó pruebas para validación de origen, dry-run sin mutaciones, bloqueo por decisiones pendientes, conversión de zona horaria y mapeo de preguntas;
- empaquetó el complemento, el perfil de ejemplo, el marketplace local, el ZIP y la trazabilidad reproducible.

Las decisiones centrales siguieron siendo humanas: enfocarse en evidencia del proceso, mantener al docente en control, prohibir publicación y operaciones destructivas, excluir datos estudiantiles y exigir confirmación explícita de la identidad del curso.

Durante el uso, GPT-5.6 ayuda al docente a razonar sobre la evidencia del curso y construir el perfil. La validación determinista impide que la capa de modelo sobrepase el alcance aprobado.

## Modelo de seguridad

- Los tokens se guardan en el keyring del sistema operativo o se entregan mediante la variable temporal **CANVAS_API_TOKEN**.
- Nunca se solicitan en el chat, se guardan en el perfil ni se versionan.
- La configuración y los reportes locales viven bajo **.canvas/**, ruta ignorada por Git.
- Las solicitudes rechazan URLs no HTTPS y redirecciones hacia un origen externo.
- Las operaciones de lectura son el comportamiento por defecto.
- La escritura exige **--confirm-course-id &lt;id&gt;** y **--confirm-unpublished**.
- Las mutaciones no se reintentan automáticamente.
- Un objeto objetivo publicado o incompatible detiene la operación.

Consulta los [lineamientos completos de seguridad](plugins/canvas-mds/skills/canvas-mds-configurar/references/security.md).

## Estructura del repositorio

~~~text
.
├── .agents/plugins/marketplace.json
├── BUILD_WEEK_PROVENANCE.md
├── dist/
│   ├── canvas-mds-portable-0.1.0.sha256.txt
│   └── canvas-mds-portable-0.1.0.zip
└── plugins/canvas-mds/
    ├── .codex-plugin/plugin.json
    ├── assets/profiles/entornos-digitales-2026.json
    ├── scripts/
    └── skills/
~~~

## Requisitos y plataformas

- Codex con soporte para marketplace de complementos y GPT-5.6 seleccionado.
- Python 3.10 o superior.
- Paquete Python **requests**.
- Paquete Python **keyring** para el flujo recomendado de credenciales.
- Una cuenta Canvas con rol docente para diagnósticos o creación en vivo.

El MVP está validado actualmente en **Windows con Python 3.12.4**. El código Python fue diseñado para ser portable a macOS y Linux, pero esas plataformas todavía no han sido verificadas para esta versión.

## Instalación

Desde la raíz del repositorio:

~~~text
python -m pip install requests keyring
codex plugin marketplace add <ruta-absoluta-a-este-repositorio>
~~~

Después de agregar el marketplace, reinicia la aplicación de escritorio de ChatGPT. En Codex (o modo Work), abre Plugins, elige el marketplace **Canvas MDS · Docentes** e instala **Canvas MDS**. Inicia una nueva tarea de Codex, selecciona GPT-5.6 y comienza con:

~~~text
$canvas-mds-configurar
~~~

Para revisar el comportamiento del marketplace y la instalación local, consulta la [documentación de complementos de OpenAI](https://developers.openai.com/codex/plugins/build).

El ZIP dentro de **dist/** entrega el mismo complemento sin necesidad de reconstruirlo.

## Prueba rápida para jueces: no requiere credenciales Canvas

Ejecuta desde la raíz del repositorio:

~~~text
python -m pip install requests keyring
python -m unittest discover -s plugins/canvas-mds/scripts -p "test_*.py" -v
~~~

Resultado esperado:

~~~text
Ran 7 tests
OK
~~~

Las pruebas cubren:

- HTTPS y validación de mismo origen;
- dry-run sin mutaciones;
- conservación de políticas confirmadas;
- rechazo de escritura con decisiones pendientes;
- fechas Canvas generadas en la zona horaria del curso;
- opciones admitidas para roles en el Classic Quiz;
- salida estructurada de la auditoría provisional.

También puede inspeccionarse el patrón técnico anonimizado en [entornos-digitales-2026.json](plugins/canvas-mds/assets/profiles/entornos-digitales-2026.json). Es un perfil de referencia y no debe aplicarse a un curso diferente.

## Verificación opcional conectada a Canvas

1. Copia [local-config.example.json](plugins/canvas-mds/skills/canvas-mds-configurar/references/local-config.example.json) a **.canvas/local.json** y completa solo URL, ID del curso y cuenta de keyring.
2. Guarda el token de forma interactiva:

   ~~~text
   python plugins/canvas-mds/scripts/store_canvas_token.py --account <cuenta-keyring>
   ~~~

3. Confirma el acceso de lectura:

   ~~~text
   python plugins/canvas-mds/scripts/canvas_mds.py doctor
   ~~~

4. Usa **$canvas-mds-adaptar** para crear y aprobar un perfil específico para ese curso sandbox.
5. Genera un dry-run sin mutaciones:

   ~~~text
   python plugins/canvas-mds/scripts/canvas_mds.py dry-run --blueprint <perfil-del-curso.json>
   ~~~

6. Solo después de revisar el plan y confirmar el ID del sandbox, crea opcionalmente la estructura no publicada:

   ~~~text
   python plugins/canvas-mds/scripts/canvas_mds_apply.py --blueprint <perfil-del-curso.json> --confirm-course-id <id> --confirm-unpublished
   ~~~

Este MVP no tiene comando de publicación.

## Limitaciones actuales

- Canvas es necesario para snapshots, auditorías, dry-runs en vivo y creación.
- El MVP admite un Classic Quiz por perfil.
- La aprobación y asociación de rúbricas sigue siendo una puerta manual antes de publicar.
- Las páginas se crean como plantillas revisables, no como contenido docente final.
- Falta validar macOS y Linux.
- Publicación, eliminación, notas, matrículas, entregas y comentarios están fuera del alcance.

## Alcance y trazabilidad de Build Week

Las necesidades de Canvas MDS surgieron de trabajo previo en el IA Workshop de la UDD, comisiones de IA de universidad y facultad, discusiones de política institucional y la dirección de la Maestría en Data Science. Ese trabajo previo estableció el problema y las restricciones; no se presenta como software de Build Week.

La ideación de esta implementación comenzó el 16 de julio de 2026. La primera sesión técnica central recuperada fue creada el 17 de julio. El complemento portable, sus tres skills, el motor determinista, las siete pruebas, el perfil de ejemplo, el paquete y la evidencia de entrega se implementaron para Build Week.

Consulta [BUILD_WEEK_PROVENANCE.md](BUILD_WEEK_PROVENANCE.md) para revisar el registro de evidencia.

- Track: **Education**
- Session ID de /feedback: **019f6fdb-32dc-70a0-a353-8640c3a29f08**
- SHA-256 del ZIP: **7f863022d884e4003245850fffe80c6267ae35a3b28db628685273ac2e11486e**

## Autor

- Germán Gómez
- Universidad del Desarrollo (UDD)
- gagomez@udd.cl
