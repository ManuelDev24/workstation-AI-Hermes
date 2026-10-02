# Consumo, costos y membresías
| Componente | Costo/consumo | Notas |
|---|---|---|
| `scripts/aiws …` (5 bots) | 0 tokens, 0 USD | `metrics.jsonl` registra `tokens: null` |
| Agente Hermes (`hermes -p aiws-* chat`) | Tokens vía **Nous Portal** (modelo `claude-sonnet-5.5`) contra tu suscripción/créditos de Portal | Una consulta SQL de prueba tomó 9 s, 2 llamadas a herramientas. Hermes puede mostrar uso con `display.show_cost` / `--usage-file` |
| Claude Code (plan Pro) | Cupo de uso del plan; **no** es una API key ni alimenta a Hermes | Sesión activa (verificada) | 
| Codex CLI (ChatGPT) | Instalado; una revisión de prueba usó ~8.5k tokens del cupo de tu plan ChatGPT | No es API ni alimenta a Hermes |
| Fallbacks de pago | **No habilitados** (`hermes fallback` sin configurar por mí) | |
## Tres cosas distintas
1. **Límites locales** (los puedo garantizar): `agent.max_turns=40`, `terminal.timeout=120`, `delegation.max_concurrent_children=1`, timeouts/filas/reintentos de aiws.
2. **Costos estimados**: solo orientativos; leer `hermes status`/panel de Portal.
3. **Topes reales del proveedor**: ninguno configurado por mí. No existe aquí un tope monetario estricto garantizado; si lo necesitas, configúralo en la consola del proveedor (límite de gasto) o usa solo bots deterministas.
Métricas: `logs/metrics.jsonl` (duración, estado, error redactado) con rotación 1 MB × 3.

## RAM
Bots deterministas: procesos cortos (decenas de MB). `aiws-dev` usa un contenedor limitado a 512 MB, efímero y con vida de 120 s (idle ≈ 2 MB). OrbStack (≈0,8 GB RSS) ya corría antes por tus otros contenedores; si no lo necesitas, ciérralo con `orbctl stop`. Terminal: Ghostty (≈75 MB). Monitor programado: sin modelo, ejecución de segundos cada 30 min.
