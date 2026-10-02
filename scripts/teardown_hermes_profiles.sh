#!/bin/sh
# Elimina SOLO los 5 perfiles aiws-* creados por setup_hermes_profiles.sh. No toca el perfil default.
set -eu
for P in aiws-analyst aiws-sql aiws-monitor aiws-dev aiws-knowledge; do
  hermes profile delete "$P" && echo "eliminado $P" || echo "omitido $P"
done
