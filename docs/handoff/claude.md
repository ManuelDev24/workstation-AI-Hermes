# Solicitar revisión o análisis a Claude (Claude Code)
Instalado: Claude Code 2.1.x (login claude.ai, plan Pro). Sesión renovada con `claude auth login` y verificada con una revisión de solo lectura (sin cambios en el proyecto). Las llamadas consumen el cupo de tu plan Pro; esta suscripción no es una API key ni alimenta a Hermes.
## Revisión de solo lectura (no modifica archivos)
```
cd state/dev/<tarea>   # o el proyecto a revisar
claude -p "Revisa los cambios (git diff baseline). Lista hallazgos concretos de corrección, seguridad y mantenibilidad con archivo:línea. No edites nada." \
  --allowedTools Read Grep Glob "Bash(git diff:*)" --max-turns 6
```
## Recuperar y verificar
Guarda la salida en `reports/`. Para cada hallazgo, reprodúcelo (prueba o comando) antes de aceptarlo; Claude puede equivocarse.
Hermes también incluye la skill `claude-code` para delegar desde una sesión de Hermes.

Nota: `--permission-mode plan` en modo `-p` devolvió una respuesta vacía de contenido («ya está completa…»); por eso el comando verificado usa solo `--allowedTools` de lectura (cualquier otra herramienta queda denegada en modo no interactivo).
