# Pendientes y acciones necesarias
| # | Bloqueo | Qué hacer (tú) |
|---|---|---|
| 1 | ~~Claude Code: token expirado~~ | Renovado y verificado. |
| 2 | ~~Codex CLI~~ | Instalado y verificado (0.160.0, sesión ChatGPT activa). Pendiente solo probar una tarea de implementación en una copia aislada. |
| 3 | ~~Pruebas con agente de Bots 1,3,4,5~~ | Hechas (ver validation.md). |
| 4 | Monitor programado | Job creado **pausado** (`aea4d41f1c35`). Para activarlo: `hermes -p aiws-monitor cron resume aea4d41f1c35`. Ver `configs/hermes-cron.proposal.md`. |
| 5 | Canales de alerta externos / bases externas | Deshabilitados. Requieren tu autorización y credenciales (`.env`, `configs/external_db.example.yaml`). |
| 6 | ~~Node LTS en shell~~ | Hecho: `fnm env --use-on-cd` en `~/.zshrc` (copia `~/.zshrc.bak-aiws-*`). |
| 7 | Aislamiento real de filesystem para agentes | Opcional: `hermes -p aiws-dev config set terminal.backend docker` (OrbStack). Implica montar la carpeta; no lo activé. |
| 8 | ~~Commit inicial~~ | Hecho. |
| 9 | Tope de gasto estricto | No hay. Configúralo en la consola del proveedor. |
| 10 | Xcode CLT | Instaladas (`/Library/Developer/CommandLineTools`). Sin acción. |
