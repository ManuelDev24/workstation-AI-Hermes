# Programación del monitor — CREADA Y PAUSADA
Job `aea4d41f1c35` (perfil `aiws-monitor`, cada 30 min, sin modelo → 0 tokens, entrega `local`). El script está en `~/.hermes/profiles/aiws-monitor/scripts/aiws-monitor.sh` (Hermes lo resuelve por perfil) y llama a `scripts/aiws monitor`. Verificado a mano: exit 0.
Hermes no permite ejecutar un job pausado (`cron run` responde «resume it before running»), así que la primera ejecución real ocurrirá al reanudarlo.
```
hermes -p aiws-monitor cron resume aea4d41f1c35    # ACTIVAR (requiere tu aprobación; corre dentro del gateway de Hermes)
hermes -p aiws-monitor cron runs                    # ver ejecuciones
hermes -p aiws-monitor cron pause aea4d41f1c35      # detener
hermes -p aiws-monitor cron remove aea4d41f1c35     # eliminar
```
