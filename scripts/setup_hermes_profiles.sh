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
