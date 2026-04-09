# AUDITORÍA CIENTÍFICA: HIPÓTESIS DEL +118.1% (BEAR44)

> **Fecha:** 2026-04-08
> **Estado:** CERRADO
> **Objetivo:** Confirmar o refutar si la versión histórica exacta de `ChacalSniper_Bear44.py` (commit `d4ca776`) logra replicar el stress test de +118.1% de Abril-Septiembre 2024 corriendo sobre el entorno actual nativo.

## 1. Hipótesis Inicial
Creíamos que la caída abrupta de rentabilidad se debía a contaminación inter-archivos o a la ejecución accidental de variantes maliciosas o con bugs (como la versión ULTRA con SL limitados). La teoría asume que si reproducimos entorno exacto con ADN exacto, volveremos a ver los retornos.

## 2. Procedimiento Técnico y Evidencia (Comandos Ejecutados)
Se reconstruyó la versión en el entorno WSL con Freqtrade nativo:
- **Estrategia cargada:** `ChacalSniper_Bear44.py` extraída literalmente del commit `d4ca776`.
- **Archivo de Parámetros:** `ChacalSniper_Bear44.json` histórico correspondiente a Época 46.
- **Validación Positiva de Ingesta:** Los logs de Freqtrade confirmaron la correcta lectura del strategy file y la carga exitosa de parámetros (ej: `rsi_bear_thresh=30`, `stoploss=-0.05`, etc).

## 3. Resultados Crudos del Backtest (Evidencia)

- **Aislamiento en Jun-Jul (20240601-20240801):**
  - Rentabilidad: **-16.41%**
  - Drawdown: **33.50%**
  - Operaciones: 759 trades.

- **Stress Test Completo Disponible (20240401-20240901) - Efectivo 2024-05-01 -> 2024-08-31:**
  - Rentabilidad: **-23.05%**
  - Drawdown: **35.27%**
  - Operaciones: 1519 trades.

## 4. Análisis de Componentes del Borde (Edge)
Del stress actual se desprende:
- El edge ganador existe: **+177.2%** por `trailing_stop_loss` y **+32.02%** por salidas ROI convencionales.
- Sin embargo, es destruido mayoritariamente por:
  - Pérdidas por `stop_loss`: **-184.3%**
  - Salidas forzadas tempranas `rsi_kill_switch_short`: **-58.53%**

## 5. Decisión / Conclusión Definitiva
1. **Descarte Técnico:** Ya descartamos que estuviéramos corriendo un archivo equivocado o que Freqtrade no tomara los parámetros. Todo eso es correcto.
2. **Refutación:** La versión histórica correcta **NO** reproduce el `+118.1%` de manera aislada con el dataset **actualmente descargable**.
3. **Causa Probable Sobreviviente:** Incompatibilidad de datos. Nuestro dataset actual comienza tarde (en mayo en vez de abril, faltando el mes más productivo) y la ventana en particular donde ocurre la gestión (mayo-julio) sufre de una activación tardía del régimen/switch.

**Regla resultante adoptada:** "Si el dataset no es estrictamente comparable a la evidencia histórica, no se tomará el resultado como una validación de quiebre algorítmico".
