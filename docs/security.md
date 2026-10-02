# Seguridad: credenciales, rutas y límites efectivos
## Credenciales
- No se guardó ningún secreto en el repo. `.env` está ignorado; `.env.example` solo trae nombres.
- Los bots deterministas no necesitan credenciales. El agente usa el login de Nous Portal ya existente de Hermes (compartido por los perfiles vía el almacén de Hermes).
- Claude y Codex mantienen autenticaciones propias e independientes; no se extrajeron ni reutilizaron tokens.
- Los logs pasan por un filtro de redacción (patrones `sk-…`, `ghp_…`, `xox…`, `password=/token=/api_key=`). Es un mejor esfuerzo, no una garantía: no pegues secretos en consultas.
- El token de Telegram del perfil `default` NO se clonó a los perfiles de bots (Hermes lo omite al clonar).
## Controles técnicos (verificados por pruebas, ver validation.md)
| Control | Efectivo |
|---|---|
| Lista de rutas con `resolve()` (bloquea `..` y symlinks) | Sí, en los 5 bots |
| Escrituras SQL | Sí: motor DuckDB `read_only` (probado con `WITH … INSERT`) + sin acceso externo (`read_csv('/etc/hosts')` falla) |
| Tamaño/filas/tiempo | Sí (configs/aiws.yaml) |
| Concurrencia | Sí: `flock` por bot (código de salida 4) |
| Originales intactos | Sí: SHA-256 antes/después (Bot 1), copia aislada (Bot 4) |
| No commit/push | Por diseño (el bot no invoca esas operaciones); no hay credenciales de git en el sandbox |
| Servidores solo en localhost | Sí en las plantillas (`127.0.0.1`); verificado con smoke test |
## Límites NO técnicos (honestidad)
- La herramienta `terminal`/`file` del agente Hermes no está confinada a rutas: un modelo que decida salirse de `scripts/aiws` puede hacerlo; mitigaciones = `approvals.mode=manual`, toolsets mínimos y revisar las aprobaciones. Para aislamiento real habría que usar `terminal.backend: docker` (OrbStack disponible) — no activado por defecto.
- Contenido de archivos/páginas es dato no confiable: ningún bot ejecuta instrucciones halladas en ellos (los bots deterministas solo calculan/buscan).
- Ningún proceso permanente propio: no hay LaunchAgents ni cron activos de la workstation.
