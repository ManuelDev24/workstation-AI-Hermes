# Propuesta de programación (NO activada)
Monitor sin modelo (costo 0): Hermes ejecuta solo el script. Requiere un script en `~/.hermes/scripts/`:
```
mkdir -p ~/.hermes/scripts && ln -s ~/Developer/AI-Workstation/scripts/aiws ~/.hermes/scripts/aiws-monitor.sh   # (el wrapper acepta args; crea uno dedicado si prefieres)
hermes -p aiws-monitor cron create "every 30m" --name aiws-monitor --no-agent --script aiws-monitor.sh --deliver local --paused
hermes -p aiws-monitor cron resume <id>      # solo cuando lo apruebes
hermes cron list ; hermes cron pause <id> ; hermes cron remove <id>
```
Nota: el job corre dentro del gateway de Hermes (ya activo en esta Mac). Verifica `hermes cron --help` antes de activarlo; el flag `--script` se resuelve bajo `~/.hermes/scripts/`.
