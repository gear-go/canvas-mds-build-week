# Seguridad de acceso

Preferir, en este orden: keyring del sistema operativo mediante `scripts/store_canvas_token.py`; variable temporal `CANVAS_API_TOKEN`; `--token-file` solo para migración transitoria fuera de carpetas sincronizadas o compartidas.

Nunca solicitar que el docente pegue el token en el chat. Nunca escribir `token`, `access_token`, encabezados `Authorization` ni contenido del keyring en perfiles, reportes, historial de comandos o archivos versionados.

La configuración `.canvas/local.json` puede contener URL, ID del curso y nombre de cuenta de keyring, pero no el secreto. Comprobar que `.canvas/`, `.env`, `*token*.txt` y `*.token` estén ignorados por Git.

Al mostrar diagnóstico, revelar solo URL base, ID de curso, ruta de reportes y si existe una fuente de credencial; no mostrar su valor.

