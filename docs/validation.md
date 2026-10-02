# Validación (1-oct-2026, datos 100 % sintéticos)
Reproducible con `scripts/verify_all.sh` → «TODO OK». Núcleo: 26 pruebas pytest; plantillas: API 3 · CLI 2 · data-app 2 · web 2 (vitest).

| Prueba (Fase 7) | Resultado esperado | Estado |
|---|---|---|
| CSV con duplicados y faltantes | 12 filas, 2 duplicados exactos, faltantes cantidad=1 y precio=1 | ✅ coincide (`test_csv_stats…`, CLI real) |
| Excel con varias hojas | hojas `ventas`(12) y `metas`(4) | ✅ |
| Texto en columna numérica / esquema | detecta `cantidad`; reporta columna ausente | ✅ |
| Pregunta SQL con resultado conocido | Este 80, Norte 2300, Oeste 120, Sur 1410; Mouse = 28 uds | ✅ (calculado a mano) |
| Escritura SQL (DROP/DELETE/INSERT/CREATE, multi-sentencia, `WITH…INSERT`) | rechazada; DB con SHA-256 idéntico | ✅ (motor read_only) |
| Lectura de archivos desde SQL (`read_csv('/etc/hosts')`) | rechazada | ✅ |
| Límite de filas y timeout SQL | truncado a N; error «tiempo máximo» | ✅ |
| Archivo ausente / cambio de esquema / ejecución fallida (monitor) | 3 tipos de alerta; 2.ª pasada sin duplicados | ✅ |
| Tarea de desarrollo con prueba verificable | baseline verde → parche → verde; diff con 2 archivos; original intacto y sin `.git` anidado | ✅ |
| Consulta documental | `politica_datos.md:3 § Retención`; «sin evidencia» para tema ajeno | ✅ |
| Entrada inválida (extensión, vacía, tamaño, nombre de tarea) | InvalidInput, exit 2 | ✅ |
| Ruta no autorizada (`/etc/hosts`, `..`, symlink de escape, proyecto `/etc`) | exit 3 | ✅ |
| Concurrencia | segundo `flock` → BusyError (exit 4) | ✅ |
| Secretos en logs/artefactos | `sk-…`, `password=…` redactados; grep del repo sin secretos reales (solo los falsos de las pruebas) | ✅ |
| Credencial de proveedor ausente | `hermes -p aiws-knowledge chat --provider openrouter` → «No API key found…», exit 1, mensaje claro | ✅ |
| Plantillas: instalación desde lockfile, pruebas, lint | API/CLI/data-app (`uv sync`, ruff, pytest) y web (`pnpm install`, vitest, `tsc -b`, vite build, oxlint) | ✅ |
| Servidores en 127.0.0.1 y parada limpia | respondieron; puertos libres tras SIGINT | ✅ |
| Jupyter local | API `/api/status` responde en 127.0.0.1:8899; puerto libre al detener | ✅ |
| Agente Hermes real (Bot 2, perfil `aiws-sql`) | ejecutó `scripts/aiws sql --canned total_por_region`; resultado correcto, con SQL y explicación | ✅ (1 consulta; 9 s) |
| Agente Hermes — Bot 1 (`aiws-analyst`) | ejecutó `analyze`; 12 filas, 2 duplicados, faltantes 1+1; hechos separados de hipótesis; original intacto | ✅ |
| Agente Hermes — Bot 3 (`aiws-monitor`) | ejecutó `monitor`; informó 2 hallazgos, 0 nuevos, 2 suprimidas; marcó repetidas | ✅ (detectó contaminación de `events.jsonl` por pruebas → corregida) |
| Agente Hermes — Bot 4 (`aiws-dev`) | `prepare`→editó solo `state/dev/agent-test`→`test` verde→`summary`; original intacto, sin commit | ✅ (detectó `.pyc` en el diff → corregido) |
| Agente Hermes — Bot 5 (`aiws-knowledge`) | «90 días», cita `politica_datos.md:3 § Retención` | ✅ |
| Codex `exec --sandbox workspace-write` implementa una tarea en copia aislada | añadió `median()` + 3 pruebas; `aiws dev test` verde; diff de 2 archivos; original intacto; sin commits (20,8k tokens) | ✅ |
| Monitor programado | job creado pausado; script ejecutado a mano exit 0; ejecución programada real pendiente de activación | ⏳ |
| Node 24 por `.node-version` | `zsh -i` dentro de `web-react` y en `~` → v24.21.0 | ✅ |
| Claude Code `-p` (revisión de solo lectura) | tras `claude auth login`: identificó el `ZeroDivisionError` de `average([])`; proyecto sin cambios. (Con `--permission-mode plan` la respuesta fue vacía de contenido → comando documentado sin plan mode) | ✅ |
| Codex CLI `exec` solo lectura | revisó `sample-repo` e identificó el `ZeroDivisionError` (8.5k tokens); proyecto sin cambios | ✅ |
## Defectos encontrados y corregidos durante la validación
Pruebas con agente: los `.pyc` aparecían en el diff del sandbox (ahora excluidos y `PYTHONDONTWRITEBYTECODE=1`, con prueba de regresión); las pruebas escribían en los `logs/` reales (ahora `AIWS_LOG_DIR` aislado por pytest). `relative_to` fallaba con salidas fuera del repo (ahora `rel()`); pandas 3 usa dtype `str` (detección de texto/esquema ajustada); `PYTHONPATH` heredado rompía `uv run` (wrapper `scripts/aiws`).
## Limitaciones conocidas del ranking documental
TF-IDF simple: favorece títulos; «¿Qué hace flock…?» devolvió secciones relacionadas pero no la más precisa (#2 en relevancia humana). Embeddings solo si se demuestra la necesidad.
