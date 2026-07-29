# AssessTrace — Evidence by Design

> Rediseña la evaluación para que el proceso de aprendizaje deje evidencia; el docente decide, la herramienta traza. Canvas MDS es su primer adaptador.

[English version](README.md) · [Índice completo de documentación en español](docs/es/README.md)

AssessTrace ayuda a diseñar la evaluación alrededor del **proceso de aprendizaje**, no solo del producto final. Su metodología **Evidence by Design** utiliza **Codex con GPT-5.6** para comprender la evidencia del curso, hacer visibles las brechas de validez, proponer alternativas viables y preservar el juicio docente en cada decisión material.

**AssessTrace** es el producto, **Evidence by Design** es su metodología pedagógica y **Canvas MDS** es el primer adaptador técnico. Canvas MDS transforma un diseño aprobado y trazable en blueprints revisables para Canvas LMS mediante un motor Python determinista: la inspección y el dry-run no realizan mutaciones, mientras que la ruta protegida solo puede crear estructuras explícitamente aprobadas y no publicadas.

El MVP y su adaptador Canvas MDS fueron diseñados para docentes del ecosistema de la Maestría en Data Science (MDS) de la Universidad del Desarrollo (UDD), pero los contratos de evidencia y la arquitectura basada en perfiles pueden admitir futuros adaptadores LMS y otras instituciones.

## El problema

La IA generativa cambia lo que una entrega final permite demostrar. Los docentes necesitan una manera práctica de rediseñar actividades, checkpoints, evidencia individual, políticas de uso de IA y secuencias de evaluación sin reconstruir manualmente cada curso en Canvas ni delegar las decisiones pedagógicas a un sistema automatizado.

AssessTrace separa:

- los lineamientos compartidos a nivel institucional y de programa;
- la evidencia extraída del programa aprobado y la planificación;
- las decisiones que todavía requieren al docente;
- las operaciones deterministas de Canvas que pueden revisarse antes de ejecutarse.

## Por qué un plugin y no una plataforma

Ya existen herramientas que resuelven partes de este problema. Algunas plataformas alojadas hacen visible el proceso de escritura, pero pueden requerir un contrato institucional adicional e incorporar un nuevo procesador para trabajos estudiantiles. Los agentes nativos de un LMS pueden generar estructuras dentro de una sola plataforma, aunque aumentan la dependencia de su licenciamiento. Las suites de alineamiento curricular permiten detectar brechas entre resultados y actividades, pero suelen operar dentro de su propio ecosistema.

AssessTrace adopta una posición más acotada y portable: no introduce una plataforma de evaluación separada. Cuando Canvas y Codex con GPT-5.6 ya cuentan con aprobación institucional, puede operar mediante servicios, políticas y credenciales controladas por la institución. No publica ni elimina contenido, excluye datos estudiantiles por diseño y separa el juicio docente de un motor determinista que rechaza escrituras no autorizadas o inseguras. Su valor no depende de ofrecer más funciones que otras alternativas, sino de reducir la superficie que una institución debe gobernar para realizar un piloto.

## Qué hace el MVP

- Lee la estructura del curso sin recuperar entregas, notas ni matrículas.
- Produce snapshots estructurales, auditorías provisionales y dry-runs sin mutaciones.
- Diagnostica qué puede y qué no puede demostrar la evaluación actual sobre el aprendizaje en un curso con IA.
- Impone una puerta de alineamiento: confirma el objetivo antes de derivar indicadores, evidencias, instrumentos, procedimientos o actividades.
- Propone alternativas de rediseño, simula fallas de validez y registra las decisiones del docente.
- Convierte el rediseño aprobado en un perfil JSON portable.
- Crea o reutiliza grupos de evaluación, una categoría de equipos, páginas, tareas, un Classic Quiz y módulos.
- Exige confirmar el ID exacto del curso Canvas antes de cualquier escritura.
- Crea todo como **no publicado** y verifica ese estado después de ejecutar.
- Se niega a escribir cuando existen decisiones pendientes, pesos incompatibles, identidad incorrecta o un objeto objetivo ya publicado.

Deliberadamente **no** publica ni elimina contenido, modifica matrículas, descarga entregas, publica comentarios ni escribe notas.

## Cómo funciona

| Capa | Responsabilidad |
| --- | --- |
| Evidencia del curso | Programa aprobado, planificación, lineamientos institucionales y decisiones explícitas del docente. |
| AssessTrace + Evidence by Design | Usa Codex con GPT-5.6 para distinguir objetivos de actividades, alinear objetivo → indicador → evidencia → instrumento → procedimiento, diagnosticar la brecha de validez y compilar decisiones confirmadas. |
| Contratos de evidencia trazables | Guardan fuentes, propuestas, decisiones docentes, evidencia de proceso, asuntos pendientes y relaciones validables sin credenciales. |
| Adaptador Canvas MDS | Compila el diseño aprobado en un perfil Canvas; su motor Python determinista valida invariantes, lee Canvas, calcula el dry-run, aplica el plan acotado y verifica el resultado. |
| API de Canvas LMS | Recibe lecturas por defecto y solicitudes POST/PUT protegidas solo después de una confirmación explícita. |

GPT-5.6 se utiliza dentro de Codex como capa de razonamiento y orquestación. El motor Python no realiza una llamada oculta a un modelo: su función es que las reglas de seguridad sean comprobables y predecibles.

## Las skills del adaptador Canvas MDS

El adaptador conserva su ID técnico, rutas, esquemas de perfil y comandos actuales para mantener la compatibilidad:

| Skill | Propósito | Comportamiento de escritura |
| --- | --- | --- |
| **$canvas-mds-configurar** | Configura URL, ID del curso, reportes locales y fuente segura de credencial; luego diagnostica la conexión. | Solo configuración local. Nunca solicita el token en el chat. |
| **$canvas-mds-redisenar** | Diagnostica la validez de la evaluación y rediseña evidencia desde el producto final hacia proceso visible, contribución individual, uso del feedback y uso responsable de IA. | Escribe artefactos locales trazables y un perfil; nunca modifica Canvas. |
| **$canvas-mds-gestionar** | Inspecciona, audita, hace dry-run y, solo tras una aprobación precisa, crea una estructura no publicada. | Lectura por defecto; la única escritura es una creación protegida, idempotente y no publicada. |

## Cómo se utilizaron Codex y GPT-5.6

Durante Build Week, Codex con GPT-5.6 aceleró el paso desde las necesidades educativas hasta AssessTrace y su adaptador Canvas MDS funcional:

- tradujo restricciones docentes, de política de IA, privacidad y evaluación a una arquitectura de tres skills;
- ayudó a separar el juicio docente de las operaciones que podían automatizarse de forma segura;
- implementó e iteró los motores Python de lectura y escritura protegida;
- generó pruebas para validación de origen, dry-run sin mutaciones, bloqueo por decisiones pendientes, conversión de zona horaria y mapeo de preguntas;
- empaquetó el complemento, el perfil de ejemplo, el marketplace local, el ZIP y la trazabilidad reproducible.

Las decisiones centrales siguieron siendo humanas: enfocarse en evidencia del proceso, mantener al docente en control, prohibir publicación y operaciones destructivas, excluir datos estudiantiles y exigir confirmación explícita de la identidad del curso.

P0.2 incorpora una puerta de alineamiento generativo. GPT-5.6 debe comprender la necesidad documentada, distinguir un objetivo de aprendizaje de las actividades para alcanzarlo, presentar alternativas cuando no exista un objetivo aprobado y detenerse para confirmación docente. Solo entonces puede derivar indicadores, evidencias, instrumentos, procedimiento, carga y finalmente actividades. El validador determinista comprueba la cadena completa.

P0.3 refuerza la semántica de esa puerta. El motor rechaza instrumentos no seleccionados, relaciones cartesianas entre componentes, actividades que amplían la cadena aprobada, rutas de fuentes que no pueden resolverse y etiquetas de evidencia superpuestas. Una prueba de regresión reconstruye la matriz todos-con-todos detectada durante la validación directa y comprueba que el validador rechaza esa falla.

P0.3.2 refuerza la primera detención diagnóstica. Toda cita `UDD-R*` o `UDD-H*` debe registrar la base de conocimiento UDD como `SRC-00`; la ausencia de hitos evaluados no puede describirse como evidencia de proceso nula cuando existe una reflexión posterior cuyos criterios no están documentados; y cada pregunta material debe conservar un identificador `Q-*` estable dentro de `manual_decisions`, sin crear artefactos antes de la confirmación docente.

P0.3.3 cierra la relación entre autoridad y traspaso operacional. Una decisión docente aplicada debe registrarse como `confirmed`, incluso cuando modifica una opción; `resolution: modified` conserva la forma en que se alcanzó la decisión. Cada asunto operacional pendiente se representa mediante un objeto estructurado `MD-*`, y el traspaso final distingue lo propuesto por GPT-5.6, lo decidido por el docente, lo verificado por el motor determinista y lo que continúa pendiente.

Durante el uso, GPT-5.6 reconcilia evidencia heterogénea, diagnostica procesos de aprendizaje invisibles, propone al menos dos diseños viables y los somete a escenarios de IA sin comprensión y contribución desigual. El docente confirma cada decisión material. La validación determinista aplica controles inspirados en la base UDD para alineamiento con RA, evidencia de proceso e individual, uso del feedback, demanda cognitiva, alternativas accesibles, ponderaciones, trazabilidad y seguridad Canvas.

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

## Instalación para pilotos desde GitHub

Cuando este repositorio es público, registra el marketplace directamente desde GitHub:

~~~text
python -m pip install requests keyring
codex plugin marketplace add gear-go/canvas-mds-build-week --ref main
~~~

También puedes instalar desde un clon local:

Desde la raíz del repositorio:

~~~text
python -m pip install requests keyring
codex plugin marketplace add <ruta-absoluta-a-este-repositorio>
~~~

Después de agregar el marketplace, reinicia la aplicación de escritorio de ChatGPT. En Codex (o modo Work), abre Plugins, elige el marketplace **Canvas MDS · Docentes** e instala **AssessTrace · Canvas MDS**. Inicia una nueva tarea de Codex, selecciona GPT-5.6 y comienza con:

~~~text
$canvas-mds-configurar
~~~

Para revisar el comportamiento del marketplace y la instalación local, consulta la [documentación de complementos de OpenAI](https://developers.openai.com/codex/plugins/build).

El ZIP dentro de **dist/** entrega el mismo complemento sin necesidad de reconstruirlo.
El paquete **assesstrace-canvas-mds-skills-only-0.1.0.zip** está reservado para el portal oficial de Plugins y no reemplaza la instalación desde el marketplace durante el piloto.

## Prueba rápida para jueces: no requiere credenciales Canvas

Ejecuta desde la raíz del repositorio:

~~~text
python -m pip install requests keyring
python -m unittest discover -s plugins/canvas-mds/scripts -p "test_*.py" -v
~~~

Resultado esperado:

~~~text
Ran 49 tests
OK
~~~

Luego ejecuta la experiencia completa para jueces, cuya interfaz y documentación están en inglés:

~~~text
python judge_demo.py
~~~

El comando valida el rediseño aprobado y el contrato de alineamiento semántico P0.3, reproduce y rechaza la matriz histórica todos-con-todos, muestra el cambio desde 95% de evidencia del producto final hacia 40% de producto final, 55% de hitos del proceso y 5% de verificación individual, y genera un resumen PASS con 24 controles pedagógicos, de trazabilidad, portabilidad y seguridad. Consulta la [experiencia de evaluación en español](JUDGE_GUIDE.es.md), que también incluye el prompt interactivo para Codex.

Las pruebas cubren:

- HTTPS y validación de mismo origen;
- dry-run sin mutaciones;
- conservación de políticas confirmadas;
- rechazo de escritura con decisiones pendientes;
- fechas Canvas generadas en la zona horaria del curso;
- opciones admitidas para roles en el Classic Quiz;
- salida estructurada de la auditoría provisional;
- separación objetivo/actividad, bloqueo de alineamiento, trazabilidad bidireccional indicador/evidencia, comparación de instrumentos, cálculo de carga y feedback utilizable;
- controles UDD de alineamiento con RA, auto/coevaluación, demanda cognitiva, actor del feedback, ciclo de respuesta y formatos alternativos;
- puertas de decisión P0.1, cálculo de carga por cohorte y rutas de salida relativas al repositorio;
- trazabilidad de fuentes UDD en HARD STOP, afirmaciones acotadas sobre evidencia del proceso e identificadores estables para preguntas y decisiones manuales en P0.3.2;
- semántica de autoridad confirmada, decisiones pendientes estructuradas y traspaso en cuatro capas en P0.3.3.

Los jueces pueden inspeccionar el contrato de razonamiento en [pedagogical-redesign.json](plugins/canvas-mds/assets/judge-case/reference/pedagogical-redesign.json), el [cambio de evidencia explicado en español](plugins/canvas-mds/assets/judge-case/reference/before-after.es.md) y el perfil compilado en [entornos-digitales-2026.json](plugins/canvas-mds/assets/profiles/entornos-digitales-2026.json). Son artefactos sanitizados de referencia y no deben aplicarse a otro curso.

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

4. Usa **$canvas-mds-redisenar** para diagnosticar, rediseñar y aprobar un perfil específico para ese curso sandbox.
5. Genera un dry-run sin mutaciones:

   ~~~text
   python plugins/canvas-mds/scripts/canvas_mds.py dry-run --blueprint <perfil-del-curso.json>
   ~~~

6. Solo después de revisar el plan y confirmar el ID del sandbox, crea opcionalmente la estructura no publicada:

   ~~~text
   python plugins/canvas-mds/scripts/canvas_mds_apply.py --blueprint <perfil-del-curso.json> --confirm-course-id <id> --confirm-unpublished
   ~~~

Este MVP no tiene comando de publicación.

## Quién opera el MVP actualmente

AssessTrace está diseñado para docentes, pero este MVP es deliberadamente un motor con barreras de seguridad y no una interfaz docente terminada. Su operación actual supone un usuario técnico capaz de trabajar con Codex, Python y confirmaciones por línea de comandos antes de cada escritura. Esta secuencia prioriza los riesgos más costosos: la calidad del razonamiento, las puertas de decisión docente y las invariantes de seguridad.

La superficie disponible para docentes es hoy la conversación en Codex conducida por las tres skills. Una interfaz no técnica y un modelo de operación acompañado por diseño instruccional o dirección de programa corresponden a pasos posteriores; no son capacidades que esta versión declare como terminadas.

## Limitaciones actuales

- Canvas es necesario para snapshots, auditorías, dry-runs en vivo y creación.
- El MVP admite un Classic Quiz por perfil.
- La aprobación y asociación de rúbricas sigue siendo una puerta manual antes de publicar.
- Las páginas se crean como plantillas revisables, no como contenido docente final.
- Falta validar macOS y Linux.
- Publicación, eliminación, notas, matrículas, entregas y comentarios están fuera del alcance.

## Alcance y trazabilidad de Build Week

Las necesidades de AssessTrace y Evidence by Design surgieron de trabajo previo en el IA Workshop de la UDD, comisiones de IA de universidad y facultad, discusiones de política institucional y la dirección de la Maestría en Data Science. Ese trabajo previo estableció el problema y las restricciones; no se presenta como software de Build Week.

La ideación de esta implementación comenzó el 16 de julio de 2026. La primera sesión técnica central recuperada fue creada el 17 de julio. El complemento portable, sus tres skills, el motor determinista, las cuarenta y nueve pruebas, el caso de rediseño centrado en el proceso, el perfil de ejemplo, el paquete y la evidencia de entrega se implementaron para Build Week.

Consulta [BUILD_WEEK_PROVENANCE.es.md](BUILD_WEEK_PROVENANCE.es.md) para revisar el registro de evidencia en español.

- Track: **Education**
- Session ID de /feedback: **019f6fdb-32dc-70a0-a353-8640c3a29f08**
- Suma de verificación: comprueba **dist/canvas-mds-portable-0.1.0.sha256.txt** junto al ZIP.

## Autor

- Germán Gómez
- Universidad del Desarrollo (UDD)
- gagomez@udd.cl
