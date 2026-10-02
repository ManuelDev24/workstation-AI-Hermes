#!/bin/sh
# Verificación completa: lint + pruebas del núcleo, de cada plantilla, y arranque/parada de servidores en localhost.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
export PATH="$PATH"; unset PYTHONPATH PYTHONHOME
FAIL=0
step() { printf '\n== %s\n' "$1"; shift; "$@" || { echo "FALLÓ: $*"; FAIL=1; }; }
step "núcleo: ruff" uv run ruff check src tests
step "núcleo: pytest" uv run pytest -q
for d in api-python cli-python data-app; do
  step "$d: ruff" sh -c "cd projects/templates/$d && uv sync -q --frozen && uv run ruff check . && uv run ruff format --check ."
  step "$d: pytest" sh -c "cd projects/templates/$d && uv run pytest -q"
done
step "web-react: install+test+typecheck+build+lint" sh -c "cd projects/templates/web-react && eval \"\$(fnm env)\" && fnm use 24 >/dev/null && pnpm install --frozen-lockfile >/dev/null && pnpm test && pnpm run build >/dev/null && pnpm lint"
step "servidores en localhost (arranque/parada sin residuos)" python3 scripts/smoke_servers.py
step "doctor" scripts/aiws doctor >/dev/null
echo; [ $FAIL -eq 0 ] && echo "TODO OK" || echo "HAY FALLOS"
exit $FAIL
