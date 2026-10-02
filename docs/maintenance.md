# Mantenimiento, copias y recuperación
- Actualizar dependencias del núcleo: `uv lock --upgrade && uv sync && scripts/verify_all.sh`. Plantillas: `uv lock --upgrade` / `pnpm update` dentro de cada una y reverificar.
- Actualizar Hermes: `hermes update` (leer notas antes). Tras actualizar: `hermes doctor` y `scripts/setup_hermes_profiles.sh` (idempotente; respalda `SOUL.md` como `SOUL.md.bak-<fecha>`).
- Node: `fnm install --lts`; fija la versión por proyecto con `.node-version`.
- Copia de seguridad: todo el estado importante es texto en el repo git local. `git log`/`git bundle create ../aiws.bundle --all`. Perfiles Hermes: `hermes profile export aiws-sql`.
- Regenerar datos: `scripts/aiws init-sample`. Limpiar sandboxes: borra manualmente `state/dev/<tarea>`.
- Reiniciar monitor: borra `state/monitor/*.json`.
- Logs: rotan solos (bot.log 1 MB × 5; últimos 50 `run-*.log`; metrics 1 MB × 3).
## Revertir todo
1. `scripts/teardown_hermes_profiles.sh` (solo perfiles `aiws-*`; el `default` no se toca).
2. `rm -rf ~/Developer/AI-Workstation` (cuando lo decidas) y, si quieres, `fnm uninstall 24`.
No se modificaron `~/.zshrc`, config global de git ni el perfil `default` de Hermes.
## Detener procesos
Servidores: Ctrl+C. Ningún proceso persistente fue creado por esta workstation (el gateway de Hermes ya corría antes: `hermes gateway --help`).
