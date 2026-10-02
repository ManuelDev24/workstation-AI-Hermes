# api-python (plantilla)
```
uv sync            # instala desde uv.lock
uv run pytest -q   # pruebas
uv run ruff check . && uv run ruff format --check .
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000   # Ctrl+C para detener
```
Config por entorno: variables `API_*` (ver `.env.example`). No incluye auth ni base de datos.
