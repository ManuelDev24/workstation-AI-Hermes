# Bots: uso, permisos y límites
Rutas y límites: `configs/aiws.yaml`. Instrucciones por bot: `bots/<bot>/INSTRUCTIONS.md` (copiadas a `SOUL.md` del perfil).
Toolsets (tras `tools disable`): todos los perfiles sin browser, image_gen, tts, computer_use, cronjob, delegation, web. Además: sql y monitor sin file ni code_execution; knowledge sin code_execution; analyst y dev conservan terminal, file y code_execution. Ver `scripts/setup_hermes_profiles.sh`.

## 1 Analista de archivos (`aiws-analyst`)
- Entrada: `.csv`/`.xlsx` ≤ 20 MB y ≤ 1 000 000 filas, solo en `data/input` o `data/sample`. Esquema opcional `--schema f.yaml` (`col: int|float|number|str`).
- Salida: `data/output/analisis-<archivo>-<run>/{informe.md,resultados.json,*.png,codigo_ejecutado.py}` + copia del informe en `reports/`.
- Informe separa «Hechos calculados» de «Interpretación (hipótesis)». Verifica SHA-256 del original antes/después.
- Limitaciones: duplicados = filas idénticas completas; detecta texto en columnas mayormente numéricas; sin fechas/outliers avanzados.
## 2 Asistente SQL (`aiws-sql`)
- Base: `data/sample/sales.duckdb` (tabla `ventas`, datos limpios sintéticos). `--canned` = preguntas verificadas; `--query` = SQL libre.
- Controles: conexión `read_only`, `enable_external_access=false`, `lock_configuration`, una sentencia, solo SELECT/WITH/DESCRIBE/SHOW, `LIMIT 1000`, timeout 10 s (`interrupt`).
- Bases externas: **deshabilitado**; plantilla `configs/external_db.example.yaml`. Con DB externa el control de solo lectura debe ser un usuario read-only del servidor.
## 3 Monitor de datos (`aiws-monitor`)
- Revisa `data/sample/monitor`: `expected.yaml` (archivos esperados), esquema de CSV (snapshot en `state/monitor/schemas.json`), `runs/*.json` con `status`.
- Alertas: `state/monitor/alerts.jsonl` y `logs/monitor/events.jsonl`; deduplicadas por huella durante `--cooldown` (3600 s) y se rearman al resolverse. Canales externos: sin código ni habilitar.
- Programación propuesta (no activada): `configs/hermes-cron.proposal.md`.
- Limitación: la línea base de esquema es la primera observación; para reiniciarla borra `state/monitor/schemas.json`.
## 4 Asistente de desarrollo (`aiws-dev`)
- **Aislamiento Docker:** el terminal de `aiws-dev` corre en `aiws-dev-sandbox:1` (Python 3.12 + pytest + ruff, `docker/dev-sandbox/Dockerfile`) con solo `state/dev` montado en `/tasks`. Flujo: `scripts/aiws dev prepare …` en el host → `cd state/dev && hermes -p aiws-dev chat -q "…"` (edita en `/tasks/<tarea>`) → `scripts/aiws dev summary …` en el host.
- `prepare` copia `projects/<p>` a `state/dev/<tarea>` con **git propio** (rama `task/<tarea>`, baseline) → el original nunca se toca y no hay git anidado. `apply` aplica un parche tras `git apply --check`. `test` ejecuta pytest en la copia. `summary` = diff vs baseline + pruebas.
- No hace commit/push/merge/despliegue en el repo real. Integrar los cambios es manual.
- Modos (arquitectura, implementación, depuración, pruebas, revisión, documentación): `bots/dev-assistant/modes.md`. Un solo bot, sin multi-agente.
- Limitaciones: `test` solo ejecuta pytest (proyectos Python); para web usa los comandos pnpm del README dentro de la copia.
## 5 Conocimiento (`aiws-knowledge`)
- Busca (TF-IDF por sección Markdown) solo en `docs/` y `data/sample/kb`; devuelve `archivo:línea § sección`; sin evidencia suficiente lo dice. Sin embeddings (no hay necesidad comprobada).
- Para añadir carpetas, edítalas explícitamente en `kb_dirs` de `configs/aiws.yaml`.
