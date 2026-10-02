# Pendientes y acciones necesarias
| # | Bloqueo | Qué hacer (tú) |
|---|---|---|
| 1 | ~~Claude Code: token expirado~~ | Renovado y verificado. |
| 2 | ~~Codex CLI~~ | Instalado y verificado: revisión de solo lectura y tarea de implementación (`median()`) en copia aislada. |
| 3 | ~~Pruebas con agente de Bots 1,3,4,5~~ | Hechas (ver validation.md). |
| 4 | Monitor programado | Job `aea4d41f1c35` **activo** (cada 30 min, sin modelo). Pausar: `hermes -p aiws-monitor cron pause aea4d41f1c35`. Ver `configs/hermes-cron.proposal.md`. |
| 5 | Canales de alerta externos / bases externas | Deshabilitados. Requieren tu autorización y credenciales (`.env`, `configs/external_db.example.yaml`). |
| 6 | ~~Node LTS en shell~~ | Hecho: `fnm env --use-on-cd` en `~/.zshrc` (copia `~/.zshrc.bak-aiws-*`). |
| 7 | ~~Aislamiento de filesystem~~ | Hecho para `aiws-dev` (Docker). Los otros 4 bots siguen en el host porque necesitan `scripts/aiws`. |
| 8 | ~~Commit inicial~~ | Hecho. |
| 9 | Tope de gasto estricto | No hay. Configúralo en la consola del proveedor. |
| 10 | Xcode CLT | Instaladas (`/Library/Developer/CommandLineTools`). Sin acción. |
| 11 | Primera ejecución programada del monitor | Prevista 00:07 AST: `hermes -p aiws-monitor cron runs`. |
| 12 | Datos reales | Copia archivos autorizados a `data/input/`; apunta `monitor_watch_dir` en `configs/aiws.yaml` si quieres vigilar otra carpeta. |
| 13 | Integración continua | `.github/workflows/ci.yml` (lint + pruebas del núcleo y plantillas en cada push). |
