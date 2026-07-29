# AssessTrace — Evidence by Design · Experiencia de evaluación

[English version](JUDGE_GUIDE.md)

AssessTrace rediseña la evaluación para que el proceso de aprendizaje deje evidencia: el docente decide y la herramienta traza. Canvas MDS es su primer adaptador.

La experiencia recomendada tiene dos partes:

1. un rediseño pedagógico interactivo con GPT-5.6 en Codex;
2. una verificación determinista, sin credenciales, del diseño aprobado y del plan para Canvas.

La verificación fuera de línea no requiere una cuenta Canvas, token, datos estudiantiles ni acceso a Internet.

## Qué parte es genuinamente generativa

AssessTrace no divide texto ni convierte información entre formatos.

GPT-5.6 debe:

- reconciliar evidencia heterogénea del curso: resultados de aprendizaje, evaluación actual, rúbrica, lineamientos de IA y restricciones docentes;
- diagnosticar la brecha de validez antes de proponer una solución;
- distinguir un objetivo demostrable de una agenda de actividades;
- proponer alternativas de objetivos observables y detenerse para confirmación docente cuando no exista un objetivo aprobado;
- derivar y auditar objetivo → indicador → evidencia → instrumento → procedimiento antes de calendarizar actividades;
- identificar procesos de aprendizaje que permanecen invisibles en productos grupales pulidos;
- formular hasta tres preguntas cuyas respuestas puedan modificar materialmente el diseño;
- proponer al menos dos alternativas viables con carga, riesgos e implicancias;
- someter la opción seleccionada a escenarios de uso de IA sin comprensión y contribución desigual del equipo;
- explicar fundamentos breves vinculados a evidencia.

El modelo no toma la decisión pedagógica final. El docente confirma, modifica o rechaza las opciones materiales. Luego, un motor determinista valida trazabilidad, ponderaciones, cobertura de resultados de aprendizaje, ciclos de feedback, evidencia individual, alternativas accesibles y barreras de seguridad para Canvas.

## Parte A · Experiencia de razonamiento interactivo

### Requisitos

- Codex con GPT-5.6.
- Este repositorio disponible localmente.
- El plugin **AssessTrace · Canvas MDS** instalado desde `plugins/canvas-mds`, o el repositorio abierto en Codex para que la skill pueda ser inspeccionada.

### Prompt

Desde la raíz del repositorio, solicita a Codex:

~~~text
Usa $canvas-mds-redisenar para analizar la evidencia sanitizada del curso
ubicada en plugins/canvas-mds/assets/judge-case/input.

Diagnostica si la evaluación actual permite establecer el aprendizaje de los
estudiantes en un curso con IA. Usa la base de conocimiento empaquetada sobre
metodologías activas UDD cuando corresponda. No inspecciones todavía la solución
de referencia. Primero muéstrame el diagnóstico vinculado a evidencia y formula
solo las preguntas docentes cuyas respuestas puedan cambiar el rediseño.

Si citas una regla UDD-R* o UDD-H*, registra la base de conocimiento UDD
empaquetada como SRC-00 en el inventario de evidencia. No equipares la ausencia
de hitos evaluados durante el proceso con 0% de evidencia del proceso cuando
exista una reflexión o defensa posterior cuyos criterios no estén documentados.
Asigna a cada pregunta material un ID estable Q-01, Q-02 o Q-03 y representa
cada asunto no resuelto mediante un objeto estructurado MD-* dentro de
manual_decisions, sin crear archivos. En HARD STOP 2, mantén la selección del
diseño como una decisión pendiente identificada. Una opción aplicada debe usar
status: confirmed; usa resolution: modified cuando modifique una alternativa.

Si la evidencia no contiene un objetivo aprobado, propone dos o tres alternativas
de objetivos observables. Detente después de presentar esas alternativas y espera
mi confirmación explícita antes de derivar indicadores o actividades.
~~~

### Qué se debe observar

Una ejecución conforme debe:

1. leer la evidencia del curso y la base de conocimiento UDD;
2. separar hechos documentados, propuestas del modelo y decisiones docentes;
3. explicar por qué un producto pulido con apoyo de IA puede ocultar comprensión insuficiente;
4. formular como máximo tres preguntas relevantes;
5. aplicar HARD STOP 1 mientras existan preguntas materiales sin respuesta, sin proponer alternativas, ponderaciones, simulaciones ni archivos en ese turno;
6. preservar los resultados aprobados o distinguir un objetivo propuesto de las actividades;
7. aplicar ALIGNMENT STOP hasta que un objetivo nuevo o revisado sea confirmado explícitamente;
8. derivar entre cuatro y seis indicadores, evidencia concreta, tres instrumentos comparados, carga realista y un procedimiento de feedback;
9. presentar al menos dos alternativas de rediseño con carga e implicancias;
10. aplicar HARD STOP 2 hasta que una opción sea seleccionada o modificada;
11. conservar el producto final auténtico e incorporar evidencia del proceso;
12. simular fallas adversariales de validez;
13. producir artefactos solo después de la confirmación docente;
14. cerrar con bloques separados para GPT-5.6, docente, motor determinista y trabajo pendiente;
15. evitar escrituras en Canvas y datos estudiantiles.

Para HARD STOP 1, se debe comprobar que la base de conocimiento UDD aparezca como `SRC-00` cuando se utilicen identificadores `UDD-R*` o `UDD-H*`; que el diagnóstico distinga entre ausencia de checkpoints evaluados durante el proceso y una reflexión posterior de criterios indeterminados; y que cada `Q-*` pendiente aparezca dentro de un objeto `manual_decisions` identificado sin crear un artefacto. En HARD STOP 2, la selección debe permanecer identificada y pendiente hasta que el docente responda. En los artefactos finales, una opción modificada se registra mediante `status: confirmed` y `resolution: modified`, nunca mediante un estado ambiguo de autoridad.

Para una revisión acotada, la interacción puede compararse con los siguientes artefactos:

| Artefacto | Qué demuestra |
| --- | --- |
| [planning-alignment.json](plugins/canvas-mds/assets/judge-case/reference/planning-alignment.json) | Objetivo confirmado, indicadores, evidencia, instrumentos comparados, carga y procedimiento de feedback. |
| [pedagogical-redesign.json](plugins/canvas-mds/assets/judge-case/reference/pedagogical-redesign.json) | Diagnóstico vinculado a evidencia, preguntas, decisiones, alternativas y pruebas adversariales. |
| [before-after.es.md](plugins/canvas-mds/assets/judge-case/reference/before-after.es.md) | Explicación breve del cambio de paradigma evaluativo. |
| [entornos-digitales-2026.json](plugins/canvas-mds/assets/profiles/entornos-digitales-2026.json) | Diseño aprobado compilado en un perfil portable de Canvas MDS. |
| [metodologias-activas-udd.md](plugins/canvas-mds/skills/canvas-mds-redisenar/references/metodologias-activas-udd.md) | Conocimiento pedagógico institucional utilizado como lineamiento trazable. |

El caso de referencia cambia desde **95% de evidencia del producto final** hacia **40% de producto final, 55% de hitos del proceso y 5% de verificación individual**. Las dos últimas categorías constituyen **60% de evidencia total distinta del producto final** sin etiquetar dos veces el componente individual.

## Parte B · Verificación automatizada

### Requisitos

- Python 3.10 o superior.
- El paquete Python `requests`.

~~~text
python -m pip install requests
~~~

No se requiere una API key de OpenAI, token de Canvas ni cuenta Canvas.

### Paso 1 · Ejecutar las pruebas

~~~text
python -m unittest discover -s plugins/canvas-mds/scripts -p "test_*.py" -v
~~~

Resultado esperado:

~~~text
Ran 49 tests
OK
~~~

Las pruebas cubren los motores de lectura y escritura protegida, el contrato de detenciones P0.1, la carga a nivel de cohorte y las rutas portables; la separación entre objetivo y actividad, la detención de alineamiento P0.2 y las barreras semánticas P0.3 para instrumentos seleccionados, relaciones no cartesianas, herencia a nivel de actividad, actores de carga y fuentes resolubles. P0.3.2 agrega regresiones de HARD STOP para fuentes UDD trazables, afirmaciones acotadas sobre evidencia del proceso e identificadores estables para preguntas y decisiones manuales. P0.3.3 agrega barreras negativas para autoridad docente ambigua y decisiones pendientes no estructuradas, además del contrato de traspaso en cuatro capas. La regresión no cartesiana reconstruye la matriz todos-con-todos detectada en la prueba directa y verifica su rechazo.

### Paso 2 · Ejecutar la demostración

~~~text
python judge_demo.py
~~~

Inicio esperado:

~~~text
AssessTrace - Evidence by Design Judge Demo
===========================================
Status: PASS
Profile: entornos-digitales-digital-innovation-studio-2026
Canvas connection used: no
Credentials required: no
Canvas mutations: 0

Assessment evidence shift:
- Final product: 95% -> 40.0%
- Process checkpoints (excluding individual verification): 0% -> 55.0%
- Individual verification: 5% -> 5.0%
- Total non-final evidence: 5% -> 60.0%
~~~

El resto de la salida informa el papel de GPT-5.6, del docente y del motor determinista, seguido de 24 comprobaciones PASS. Estas incluyen la reproducción y el rechazo de la matriz histórica todos-con-todos, además de las barreras de alineamiento semántico y fuentes portables de P0.3.

Para obtener un resultado legible por máquinas:

~~~text
python judge_demo.py --json
~~~

## Flujo de evidencia

~~~text
Evidencia sanitizada del curso + base de conocimiento UDD
                    |
                    v
AssessTrace + GPT-5.6: diagnóstico vinculado a evidencia + preguntas
                    |
                    v
HARD STOP 1 -> respuestas docentes
                    |
                    v
Objetivo confirmado o alternativas -> ALIGNMENT STOP
                    |
                    v
Indicadores -> evidencia -> instrumentos comparados -> procedimiento
                    |
                    v
Alternativas con carga de cohorte -> HARD STOP 2
                    |
                    v
Selección docente -> simulación adversarial
                    |
                    v
Artefacto trazable + perfil portable del curso
                    |
                    v
AssessTrace: validación pedagógica y de seguridad determinista
                    |
                    v
Canvas MDS: plan de dry-run sin mutaciones
~~~

Código de producción utilizado por la verificación fuera de línea:

| Archivo | Función |
| --- | --- |
| [judge_demo.py](judge_demo.py) | Demostración en inglés sin credenciales. |
| [process_evidence.py](plugins/canvas-mds/scripts/process_evidence.py) | Validación y métricas de evaluación centrada en el proceso. |
| [planning_alignment.py](plugins/canvas-mds/scripts/planning_alignment.py) | Validación determinista P0.3 de alineamiento semántico, instrumentos y carga. |
| [canvas_mds_apply.py](plugins/canvas-mds/scripts/canvas_mds_apply.py) | Validador de perfiles y motor de escritura protegida en Canvas. |
| [canvas_mds.py](plugins/canvas-mds/scripts/canvas_mds.py) | Motor de lectura y planificador de dry-run. |
| [test_process_evidence.py](plugins/canvas-mds/scripts/test_process_evidence.py) | Pruebas de barreras pedagógicas informadas por UDD. |
| [test_planning_alignment.py](plugins/canvas-mds/scripts/test_planning_alignment.py) | Regresiones para objetivo, evidencia, instrumento, procedimiento y detención de alineamiento. |
| [test_skill_contract.py](plugins/canvas-mds/scripts/test_skill_contract.py) | Regresiones P0.1 para detenciones de decisión, carga de cohorte y rutas portables. |

## Por qué el snapshot de Canvas es sintético

Un snapshot real podría exponer estructura interna de un curso. El snapshot sintético no contiene personas, entregas, calificaciones, matrículas, tokens ni identificadores institucionales.

Solo el límite de lectura es sintético. El validador de rediseño, el validador de perfiles de producción, el planificador de acciones, el conteo de objetos, las comprobaciones de estado no publicado y la verificación de cero mutaciones son funciones reales de producción.

## Qué no demuestra esta experiencia

La experiencia no demuestra que:

- una cuenta evaluadora tenga acceso a una instancia institucional de Canvas;
- todos los endpoints estén habilitados en una instalación específica;
- el contenido docente final o las rúbricas cuenten con aprobación local;
- un curso esté listo para publicarse;
- GPT-5.6 deba calificar estudiantes o inferir autoría.

Estos puntos permanecen como barreras explícitas de revisión operacional, institucional y docente.

## Ruta opcional con un sandbox activo

Un evaluador con un sandbox desechable de Canvas y permisos docentes puede seguir la [verificación opcional conectada](README.es.md#verificación-opcional-conectada-a-canvas).

La ruta activa se mantiene en modo de lectura mediante `doctor`, `snapshot`, `audit` y `dry-run`. La creación protegida es opcional, exige confirmación explícita del curso y solo crea objetos no publicados.
