# AI-Workstation

![CI](https://github.com/ManuelDev24/workstation-AI-Hermes/actions/workflows/ci.yml/badge.svg)

Workstation para análisis de datos, desarrollo y bots (Hermes Agent + Codex/Claude de forma manual/oficial).
Mac M4 Pro · macOS 26 · Python 3.12 (uv) · Node 24 LTS (fnm). Todo local; nada expuesto a Internet.

## Inicio rápido
```sh
cd ~/Developer/AI-Workstation
scripts/aiws doctor            # diagnóstico del entorno
scripts/aiws selftest          # 26 pruebas deterministas
scripts/verify_all.sh          # verificación completa (núcleo + plantillas + servidores)
```
`scripts/aiws` fija el entorno correcto (ignora `PYTHONPATH` heredado de Hermes). Si usas `uv run aiws` directamente, haz `unset PYTHONPATH` antes.

## Bots (comandos exactos)
| Bot | Perfil Hermes | Comando |
|---|---|---|
| 1 Analista de archivos | `aiws-analyst` | `scripts/aiws analyze data/sample/ventas.csv` |
| 2 Asistente SQL | `aiws-sql` | `scripts/aiws sql --canned total_por_region` · `--query "SELECT …"` |
| 3 Monitor de datos | `aiws-monitor` | `scripts/aiws monitor` |
| 4 Asistente de desarrollo | `aiws-dev` | `scripts/aiws dev prepare --project sample-repo --task X` → `dev apply/test/summary` |
| 5 Conocimiento | `aiws-knowledge` | `scripts/aiws kb "pregunta"` |

Con agente (usa tu modelo configurado): `hermes -p aiws-sql chat -q "…"`. Detalle en `docs/bots.md`.
Datos de prueba: `scripts/aiws init-sample` (regenera `data/sample/`). Pon tus archivos autorizados en `data/input/`.

## Proyectos de software
| Tipo | Crear | Instalar + verificar | Ejecutar (solo 127.0.0.1) |
|---|---|---|---|
| API Python (FastAPI) | `scripts/new_project.sh api-python mi-api` | `cd projects/mi-api && uv sync && uv run pytest -q && uv run ruff check .` | `uv run uvicorn app.main:app --host 127.0.0.1 --port 8000` |
| Web (React+TS+Vite) | `scripts/new_project.sh web-react mi-web` | `cd projects/mi-web && pnpm install && pnpm test && pnpm run build && pnpm lint` | `pnpm dev` (puerto 5173) |
| CLI Python | `scripts/new_project.sh cli-python mi-cli` | `cd projects/mi-cli && uv sync && uv run pytest -q && uv run ruff check .` | `uv run mycli archivo.txt` |
| App de datos | `scripts/new_project.sh data-app mi-datos` | `cd projects/mi-datos && uv sync && uv run pytest -q && uv run ruff check .` | `uv run dataapp --serve` (puerto 8501) |

Detén cualquier servidor con Ctrl+C (verificado: sin procesos ni puertos residuales). Plantillas = base de desarrollo, **no** aplicaciones listas para producción.
Node: `~/.zshrc` carga `fnm` (LTS 24 por defecto y `.node-version` por proyecto).
Ejemplo requisito→implementación→prueba→revisión→entrega: `docs/example-flow.md`.

## Jupyter
`cd ~/Developer/AI-Workstation && unset PYTHONPATH && uv run jupyter lab --no-browser --ip=127.0.0.1 --notebook-dir=notebooks` (Ctrl+C para detener).

## Documentación
`docs/`: architecture · inventory · bots · security · costs · maintenance · validation · pending · example-flow · handoff/{codex,claude}.
