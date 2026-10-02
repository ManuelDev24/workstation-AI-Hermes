# Arquitectura
```
~/Developer/AI-Workstation (repo git local, sin remoto)
├─ src/aiws/            núcleo + 5 bots deterministas (Python)   ← los controles de seguridad viven AQUÍ
├─ scripts/             aiws (wrapper), verify_all, new_project, setup/teardown de perfiles Hermes, smoke_servers
├─ configs/aiws.yaml    rutas y límites explícitos (sin secretos); plantillas de DB externa y cron
├─ bots/<bot>/          INSTRUCTIONS.md (→ SOUL.md del perfil Hermes), modes.md y tareas del bot dev
├─ data/{sample,input,output}  datos sintéticos · entradas autorizadas · resultados
├─ projects/            sample-repo (ejemplo del bot dev) y templates/ (api-python, web-react, cli-python, data-app)
├─ logs/ state/         logs rotados y metrics.jsonl · bloqueos, alertas, sandboxes (ignorados por git)
└─ docs/ tests/ notebooks/ reports/
```
## Decisión clave: bot = perfil Hermes + CLI determinista
Según la documentación de Hermes, un *bot* es un **perfil** (`~/.hermes/profiles/<nombre>/`) con config, memoria, skills, credenciales e historial propios. Creados: `aiws-analyst`, `aiws-sql`, `aiws-monitor`, `aiws-dev`, `aiws-knowledge`.
El agente (LLM) decide qué preguntar/ejecutar; el trabajo y las restricciones se hacen en `scripts/aiws <bot>`: funciona sin modelo, es reproducible y se prueba con pytest.
## Qué aísla Hermes y qué no
- Aísla por perfil: config, `SOUL.md`, memoria, skills, sesiones, toolsets, `terminal.cwd`, aprobaciones.
- **No aísla el sistema de archivos**: la herramienta `terminal` de un perfil puede leer cualquier ruta de tu usuario. Las instrucciones en lenguaje natural NO son una barrera. Las barreras técnicas reales son: lista de rutas con resolución de symlinks (`authorize`), DuckDB `read_only`, límites de tamaño/filas/tiempo, bloqueo por archivo, sandbox git en copia y `approvals.mode=manual`.
## Modelo de ejecución
`run_bot()`: bloqueo `flock` por bot → timeout (SIGALRM) → hasta `retries` reintentos solo en errores de E/S → log por ejecución + rotativo por bot (secretos redactados) → métrica JSONL.
Códigos de salida: 0 ok · 1 error · 2 entrada inválida · 3 ruta no autorizada · 4 bot ocupado · 5 timeout.
