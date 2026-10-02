# Modos del bot de desarrollo
Cada tarea: resultado esperado + criterios de aceptación → inspeccionar → plan breve → cambios pequeños → verificar → revisar diff → entregar instrucciones y limitaciones.

| Modo | Qué hace | Verificación mínima |
|---|---|---|
| Arquitectura | Requisitos → propuesta técnica, decisiones, tareas | Documento en docs/; sin código |
| Implementación | Construye en la copia aislada | `aiws dev test` verde + diff revisado |
| Depuración | Reproduce con una prueba que falla, halla causa, corrige | La prueba nueva falla antes y pasa después |
| Pruebas | Añade pruebas de comportamiento/regresión | pytest verde; fallo si se revierte el cambio |
| Revisión | Hallazgos concretos de corrección, seguridad, mantenibilidad (archivo:línea) | Cada hallazgo reproducible |
| Documentación | README, ejemplos, decisiones | Comandos documentados ejecutados |
Sin commits/push/PR/despliegues automáticos: quedan preparados para tu orden.
