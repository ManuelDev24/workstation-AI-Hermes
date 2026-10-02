#!/bin/sh
# Uso: scripts/new_project.sh <api-python|web-react|cli-python|data-app> <nombre>
# Copia la plantilla a projects/<nombre> (sin .venv/node_modules/dist). No ejecuta git init ni instala nada.
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
T="$ROOT/projects/templates/${1:?tipo}"; N="${2:?nombre}"
[ -d "$T" ] || { echo "plantilla desconocida: $1" >&2; exit 2; }
case "$N" in *[!a-zA-Z0-9_-]*|"") echo "nombre inválido" >&2; exit 2;; esac
D="$ROOT/projects/$N"; [ -e "$D" ] && { echo "ya existe: $D" >&2; exit 2; }
mkdir -p "$D" && (cd "$T" && tar --exclude=.venv --exclude=node_modules --exclude=dist --exclude=__pycache__ --exclude=.pytest_cache --exclude=.ruff_cache -cf - .) | (cd "$D" && tar -xf -)
echo "creado $D  -> siguiente: cd projects/$N && (uv sync | pnpm install) && ver README.md"
