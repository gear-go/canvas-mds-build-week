---
name: canvas-mds-adaptar
description: Convierte programa, planificación, guía MDS y decisiones docentes en un perfil portable de curso para Canvas. Usar al iniciar o actualizar un curso, comparar lineamientos comunes con particularidades del ramo, resolver preguntas de evaluación, fechas, IA y datos, o preparar un blueprint revisable antes del dry-run.
---

# Canvas MDS · Adaptar

Separa el estándar común MDS de las decisiones propias de cada curso y produce un perfil JSON trazable, sin modificar Canvas.

## Fuentes y autoridad

1. Identificar programa aprobado, planificación vigente, guía institucional y decisiones confirmadas del docente.
2. Tratar el programa aprobado como autoridad para resultados y ponderaciones; usar la planificación para secuencia y fechas; registrar contradicciones como decisiones pendientes.
3. No trasladar fechas, porcentajes, políticas ni nombres desde el ejemplo de Entornos Digitales a otro curso sin evidencia explícita.
4. Leer [references/profile-schema.md](references/profile-schema.md) antes de crear o editar el perfil.

## Flujo

### 1. Inventariar

Localizar los documentos relevantes en la carpeta del curso. Para DOCX o PDF, extraer texto y tablas preservando encabezados y estructura. Registrar sus rutas relativas en `source_files`.

### 2. Comparar y preguntar

Construir una matriz interna con resultados de aprendizaje, módulos/sesiones, evaluaciones, incidencia, fechas, modalidad individual/grupal, rúbricas, atraso/recuperación, uso de IA y clasificación de datos. Preguntar solo por decisiones no resolubles desde los documentos.

### 3. Crear perfil

Copiar [assets/course-profile-template.json](assets/course-profile-template.json) a `canvas_profiles/<slug-del-curso>.json`. Reemplazar todos los ejemplos y completar:

- términos distintivos de identidad del curso;
- grupos que sumen 100;
- actividades y fechas en `America/Santiago` u otra zona declarada;
- páginas, módulos y relación de cada actividad;
- Classic Quiz y puntos de sus preguntas;
- políticas confirmadas y decisiones pendientes.

El perfil de ejemplo probado está en `../../assets/profiles/entornos-digitales-2026.json`; usarlo solo como patrón técnico.

### 4. Validar con el docente

Mientras falte una definición, mantenerla en `manual_decisions`. Vaciar esa lista solo con confirmación explícita. Las rúbricas aprobadas son una puerta previa a publicar, aunque el MVP pueda crear borradores no publicados.

### 5. Entregar

Resumir qué proviene de cada fuente, qué adaptaciones se hicieron, las decisiones confirmadas y las pendientes. Recomendar `$canvas-mds-gestionar` para dry-run; no ejecutar escritura desde este skill.

## Portabilidad

No incluir URL, ID de Canvas, token, nombres de estudiantes, entregas, notas ni reportes locales en el perfil. Los cambios comunes deben ir al plugin; las particularidades quedan en el perfil del curso.

