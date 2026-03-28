---
description: Pipeline de Hyperopt Rápido (100 épocas)
---
# WORKFLOW: HYPERSPRINT CHACAL

Este flujo automatiza la búsqueda de parámetros óptimos para la lógica de atraso.

1. **ENTORNO:** Ejecutar localmente en Docker o Python nativo.
2. **FILTRO:** Usar los últimos 15 días (**2026-03-08** a **2026-03-23**).
3. **EJECUCIÓN:**
   ```bash
   freqtrade hyperopt --epochs 100 --timerange 20260308-20260323 --strategy ChacalPure_Adaptativo --spaces buy sell --loss SharpeHyperOptLoss
   ```
4. **RESULTADO:**
   - Si el 'Total Profit' es positivo, presentar el resumen por pares.
   - Guardar el nuevo `.json` en `strategies/ChacalPure_Adaptativo.json`.
5. **NOTIFICACIÓN:** 
   - Reportar: "Hyperopt completado. Nuevo Profit esperado: X%. Drawdown máximo: Y%."
