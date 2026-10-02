# Entregar una tarea de implementación a Codex (flujo manual)
Estado: **Codex CLI 0.160.0 instalado** (`brew install --cask codex`, cask oficial) y con sesión ChatGPT activa (`codex login status`). Su autenticación es independiente de Claude y del proveedor `openai-codex` de Hermes. Consume el cupo de tu plan ChatGPT.
Verificado: `codex exec --sandbox read-only` revisó `projects/sample-repo` sin modificarlo.
Nota: Codex avisa de un ajuste `mcp_servers.Neon.type` ignorado en `~/.codex/config.toml` (no lo toqué; es ruido inofensivo).
## Procedimiento
1. Prepara la copia aislada: `scripts/aiws dev prepare --project <proyecto> --task <nombre>`.
2. En `state/dev/<nombre>` abre Codex y pega la plantilla:
```
TAREA: <resultado esperado en una frase>
CRITERIOS DE ACEPTACIÓN: <lista verificable>
ALCANCE: solo archivos bajo este directorio. Sin commit/push/instalaciones globales/red.
VERIFICACIÓN: ejecuta `pytest -q` y muestra la salida.
ENTREGA: resumen de cambios y limitaciones. No hagas commit.
```
3. Recupera y verifica desde Hermes: `scripts/aiws dev summary --task <nombre>` (diff + pruebas). Revisa el diff antes de copiar nada al proyecto original.

## Modo no interactivo (verificado)
```
cd state/dev/<tarea>
codex exec --sandbox workspace-write --skip-git-repo-check "<plantilla de tarea>"   # puede editar solo dentro de la copia
codex exec --sandbox read-only "<pregunta de revisión>"                              # solo lectura
```
Nunca uses `--dangerously-bypass-approvals-and-sandbox`.

Verificado de extremo a extremo: Codex añadió `median()` con pruebas en una copia aislada; `scripts/aiws dev summary` entregó diff y pruebas en verde.
