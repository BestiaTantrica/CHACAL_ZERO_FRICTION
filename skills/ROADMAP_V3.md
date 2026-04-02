# Estado Volume Hunter (2026-04-01)
- Hyperopt 100 épocas completado: +0.71% (época 90)
- Backtest: -17.44% (mejoró de -22.73%)
- Time guard implementado (06-20 UTC)
- Hyperopt 28 pares en progreso: Jul-Nov 2025, 123 días
- 28 pares con datos desde Sep 2025, solo BTC/ETH para 2024

---

# Sprint Adaptabilidad de Transiciones (prioridad máxima)

## Fase A: Validadores de régimen
- Implementar validador intra-par (confirmación de pivote con histéresis)
- Implementar validador inter-pares (correlación con altcoins)
- Implementar validador de contexto BTC (volatilidad + liquidez)

## Fase B: Filtro anti-falso quiebre
- Histéresis configurable (ej: 0.5% de rango muerto)
- Confirmación multi-vela dinámica (2-5 velas según volatilidad)
- Rechazo de señales en zonas de alta ruido

## Fase C: Ejecución escalonada
- Entradas escalonadas ("breadcrumb entries") con intervalo dinámico
- Anti-crowding: no abrir todos los shorts simultáneamente
- Gestión de riesgo por entrada escalonada

## Fase D: Gestión de pivote
- Cierres rápidos cuando se invalida el escenario short
- Transición short→long con confirmación de reversión
- Transición long→short con validación reforzada

## Fase E: Optimización focalizada
- Hyperopt en espacio de parámetros short
- Validación A/B por tags (ej: "short_optimized")
- Métricas de adaptabilidad (tasa de falsos quiebres)