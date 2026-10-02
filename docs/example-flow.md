# Ejemplo completo: requisito → implementación → prueba → revisión → entrega
**Requisito:** `average([])` hoy lanza `ZeroDivisionError`; debe lanzar `ValueError` con mensaje claro.
**Criterios:** (1) `average([1,2,3]) == 2` sigue pasando; (2) lista vacía → `ValueError` «al menos un valor»; (3) el proyecto original no cambia.
```sh
scripts/aiws dev prepare --project sample-repo --task empty-avg                     # copia aislada + git propio
scripts/aiws dev test    --task empty-avg                                           # baseline verde
scripts/aiws dev apply   --task empty-avg --patch bots/dev-assistant/tasks/empty-average.patch   # implementación (parche de ejemplo)
scripts/aiws dev summary --task empty-avg                                           # diff + pruebas = revisión y entrega
```
En una sesión con agente, el modelo edita en `state/dev/empty-avg` en lugar de aplicar el parche. **Revisión:** leer el diff (2 archivos, +9 líneas) y, opcionalmente, pedir revisión a Claude (`docs/handoff/claude.md`). **Entrega:** el diff y el resultado de pruebas; integrar al proyecto real y hacer commit es decisión tuya. Ejecutado y verificado en esta Mac (pruebas verdes, original intacto).
