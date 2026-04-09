# AUDITORÍA FINAL: FILTROS MACRO VS AIRBAG 1M

> **Fecha:** 2026-04-09
> **Estado:** CERRADO
> **Objetivo:** Determinar si la pérdida del edge provenía del dataset faltante, del filtro macro o del Kill Switch de 1 minuto.

## 1. Hallazgo Raíz: Dataset Estratégico Recuperado

Se confirmó que el problema inicial de replicación venía de la ausencia del dataset de abril 2024.

- Dataset re-descargado limpio en WSL/Freqtrade nativo.
- Timeframes verificados: `1m`, `5m`, `1h`.
- Arranque confirmado: `2024-04-01 00:00:00`.
- Estado Binance: **sin bloqueo explícito** durante la descarga.

## 2. Fase 2 — Backtest sin Micro-Gestión (No1m)

Se creó `ChacalSniper_Bear_No1m.py` apagando la micro-gestión de salida para aislar el edge base.

### Resultado

- **Profit:** `+154.82%`
- **Drawdown:** `64.26%`
- **Drawdown Period:** `2024-07-05 09:09:00` → `2024-07-21 20:29:00`
- **Liquidaciones:** `25`

### Veredicto

El edge base del bot **sigue vivo e intacto**. El trailing stop conserva una capacidad de generación de profit extraordinaria.

Pero al desactivar la protección micro de `1m`, el sistema queda expuesto a pumps violentos y entra en una zona de destrucción por liquidaciones, especialmente cuando el filtro macro permite cortos en contextos laterales o ambiguos.

## 3. Fase 3 — Endurecimiento Macro con EMA200

Se modificó `ChacalSniper_Bear_No1m.py` para exigir que BTC en `1h` esté:

- debajo de `EMA50`, y
- debajo de `EMA200`

además del filtro de volatilidad macro existente.

### Resultado

- **Profit:** `+101.79%`
- **Drawdown:** `58.88%`
- **Drawdown Period:** `2024-07-05 09:09:00` → `2024-07-16 16:04:00`
- **Liquidaciones:** `23`

## 4. Impacto EMA200 Macro

El endurecimiento con EMA200 **mejora parcialmente** el comportamiento del switch, reduciendo exposición y bajando levemente el daño:

- Profit cae de `+154.82%` a `+101.79%`
- Drawdown baja de `64.26%` a `58.88%`
- Liquidaciones bajan de `25` a `23`

### Conclusión Forense

La EMA200 macro ayuda, pero **no resuelve** la herida crítica.

El problema mortal no era solo el scanner macro: también queda demostrado que **apagar o excluir el Kill Switch de 1m es suicida** en un sistema short x5 sobre futuros.

El bot necesita la micro-vela de `1m` para ejecutar salidas de emergencia antes de que un pump lo liquide.

## 5. Veredicto Final

1. **El edge base es real y extremadamente rentable.**
2. **La ausencia del dataset de abril era la causa principal de la falsa pérdida de replicación.**
3. **El filtro EMA200 macro mejora, pero no salva por sí solo.**
4. **El Kill Switch de 1m es imprescindible para supervivencia operativa.**

## 6. Próxima Misión Operativa

La siguiente etapa debe concentrarse en el archivo estable original `ChacalSniper_Bear44.py`:

### A) Stoploss anti-liquidación

Revisar y endurecer márgenes de stoploss por par para evitar liquidaciones plenas, con foco explícito en:

- `ADA/USDT:USDT`
- `BNB/USDT:USDT`

### B) Re-activación y optimización del Kill Switch 1m

Reintegrar el Kill Switch de `1m` con el entorno limpio actual, sabiendo que:

- el dataset de abril ya está correcto,
- WSL/Freqtrade nativo está operativo,
- y el edge macro/base ya fue validado.

## 7. Decisión Adoptada

**Regla operativa resultante:**

> “El edge del Sniper Bear no se toca. La prioridad es blindar supervivencia: stoploss por par + Kill Switch 1m optimizado.”