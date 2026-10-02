# Inventario (1-oct-2026)
| Elemento | Estado |
|---|---|
| Equipo | MacBook Apple M4 Pro, 24 GB RAM, macOS 26.6.2, arm64; disco 460 GB, ~353 GB libres |
| Shell / gestores | zsh · Homebrew 7.0.7 · uv 0.11.8 · pnpm 12.6.0 · npm 11.19 · fnm 1.39 |
| Git | 2.54 (Apple); identidad global ya configurada (no se alteró) |
| Python | sistema 3.9.6 (no se usa) · Homebrew 3.12.14 (usado por el venv) |
| Node | 26.8.2 (Homebrew, *Current*, no LTS) + **24.21.0 LTS instalado con fnm** para proyectos |
| Editor | VS Code 1.139 (reutilizado) |
| Hermes | v0.21.5 (2026.9.24); proveedor Nous Portal, modelo `anthropic/claude-sonnet-5.5`; gateway ya activo antes de empezar |
| Claude Code | 2.1.177, login claude.ai plan Pro, sesión activa |
| Codex CLI | 0.160.0 instalado con `brew install --cask codex` (cask oficial → github.com/openai/codex); sesión ChatGPT ya activa (`codex login status`) |
| Docker (OrbStack) | instalado, no se usa ni se modificó |
| Herramientas extra | DuckDB CLI 1.5.2, gh 2.101, ruff vía uv |
| Credenciales (solo presencia) | OPENAI/ANTHROPIC/OPENROUTER/GITHUB en entorno: no disponibles. Hermes: Nous Portal con sesión; existe un token de Telegram en `~/.hermes/.env` (no tocado ni copiado a los perfiles de bots) |
| Puertos en escucha previos | 3000 (node de otra app), 5000/7000 (AirPlay), apps de escritorio; ninguno de la workstation |
## Incompatibilidades detectadas
- `PYTHONPATH` heredado de Hermes (apunta a Python 3.14) rompe `uv run` → resuelto con `scripts/aiws` y `env -u PYTHONPATH`.
- Node 26 es *Current*, no LTS → LTS 24 aislado por fnm; no se cambió el Node global.
- Pandas 3.x / DuckDB 1.5 resueltos por uv; código probado con esas versiones.
- `sed -i` y `timeout` de GNU no existen en macOS: scripts usan sintaxis portable.
