---
name: canvas-mds-configurar
description: Configura de forma segura el adaptador Canvas MDS de AssessTrace desde una carpeta local. Usar cuando un docente necesite conectar Canvas, registrar URL e ID de curso, guardar o migrar su token sin exponerlo, comprobar permisos, listar cursos o diagnosticar la conexión antes de cualquier auditoría o cambio.
---

# AssessTrace · Configurar el adaptador Canvas MDS

Configura el contexto local reutilizable de un docente sin incluir secretos en el plugin, el chat ni archivos compartidos.

## Reglas obligatorias

1. Leer [references/security.md](references/security.md) antes de manejar acceso.
2. No pedir nunca el valor del token en el chat ni como argumento de línea de comandos.
3. Guardar URL, ID y cuenta de keyring en `.canvas/local.json`; jamás guardar allí el token.
4. Mantener `.canvas/`, `.env`, `*token*.txt` y `*.token` fuera de Git.
5. Ejecutar solo lecturas hasta que `doctor` confirme curso y permisos.

## Flujo

### 1. Reunir datos no secretos

Solicitar al docente la URL institucional de Canvas, ID numérico o código del curso y una etiqueta de cuenta para keyring. Si falta el ID, configurar primero la URL y usar `list-courses` para que el docente identifique el curso.

### 2. Crear configuración local

Copiar [references/local-config.example.json](references/local-config.example.json) a `.canvas/local.json` en la carpeta del curso y reemplazar solo los valores no secretos. Crear o actualizar `.gitignore` con las exclusiones de seguridad.

### 3. Registrar la credencial

Preferir el keyring del sistema:

`python <plugin>/scripts/store_canvas_token.py --account <cuenta>`

El comando solicita el token de forma interactiva y oculta. Si `keyring` no está disponible, usar `CANVAS_API_TOKEN` únicamente como variable temporal del proceso. `--token-file` es compatibilidad transitoria, no la configuración recomendada.

### 4. Verificar

Desde la carpeta del curso ejecutar:

- `python <plugin>/scripts/canvas_mds.py doctor`
- `python <plugin>/scripts/canvas_mds.py list-courses` cuando se necesite resolver el ID.

Confirmar al docente URL, ID, nombre/código devuelto por Canvas y capacidades estructurales. No imprimir ni registrar la credencial.

## Salida

Entregar un estado breve: `CONFIGURADO`, `CONFIGURACION_INCOMPLETA` o `SIN_PERMISOS`, con el siguiente paso seguro. No continuar a escritura si el curso no fue identificado inequívocamente.

