#!/bin/sh
# Configura los 5 perfiles Hermes de los bots (idempotente). Usa solo comandos documentados:
# hermes profile create / tools disable / config set. Respalda SOUL.md antes de reemplazarlo.
# Reversión: scripts/teardown_hermes_profiles.sh
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HH="${HERMES_HOME:-$HOME/.hermes}"
TS="$(date +%Y%m%d-%H%M%S)"
COMMON_OFF="browser image_gen tts computer_use cronjob delegation web"
# perfil|directorio-del-bot|toolsets extra a desactivar
for spec in "aiws-analyst|file-analyst|" "aiws-sql|sql-assistant|file code_execution" \
            "aiws-monitor|data-monitor|file code_execution" "aiws-dev|dev-assistant|" \
            "aiws-knowledge|knowledge|code_execution"; do
  P="${spec%%|*}"; rest="${spec#*|}"; D="${rest%%|*}"; EXTRA="${rest#*|}"
  hermes profile list 2>/dev/null | grep -q "$P" || hermes profile create "$P" --clone --no-alias \
      --description "AI-Workstation: $D" >/dev/null
  # shellcheck disable=SC2086
  hermes -p "$P" tools disable $COMMON_OFF $EXTRA >/dev/null
  hermes -p "$P" config set approvals.mode manual >/dev/null
  hermes -p "$P" config set agent.max_turns 40 >/dev/null
  hermes -p "$P" config set terminal.cwd "$ROOT" >/dev/null
  hermes -p "$P" config set terminal.timeout 120 >/dev/null
  hermes -p "$P" config set delegation.max_concurrent_children 1 >/dev/null
  SOUL="$HH/profiles/$P/SOUL.md"
  [ -f "$SOUL" ] && cp "$SOUL" "$SOUL.bak-$TS"
  cp "$ROOT/bots/$D/INSTRUCTIONS.md" "$SOUL"
  echo "ok $P"
done
# aiws-dev: terminal en contenedor Docker (OrbStack). Solo ve state/dev montado en /tasks; no ve el resto del disco.
P=aiws-dev
docker image inspect aiws-dev-sandbox:1 >/dev/null 2>&1 || docker build -q -t aiws-dev-sandbox:1 "$ROOT/docker/dev-sandbox" >/dev/null
mkdir -p "$ROOT/state/dev"
hermes -p "$P" config set terminal.backend docker >/dev/null
hermes -p "$P" config set terminal.docker_image aiws-dev-sandbox:1 >/dev/null
hermes -p "$P" config set terminal.docker_mount_cwd_to_workspace false >/dev/null
hermes -p "$P" config set terminal.docker_volumes "[\"$ROOT/state/dev:/tasks\"]" >/dev/null
hermes -p "$P" config set terminal.cwd /tasks >/dev/null
hermes -p "$P" config set terminal.container_memory 512 >/dev/null      # poca RAM
hermes -p "$P" config set terminal.container_persistent false >/dev/null
echo "ok $P (docker)"
