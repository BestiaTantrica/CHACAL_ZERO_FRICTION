# 📊 CHACAL MASTER ESTADO — TABLERO GLOBAL

> **Última actualización:** 2026-04-09
> **Estado:** Avance Crítico. Dataset de Abril recuperado. Edge del bot verificado en WSL (+155%).

---

## 🚦 ESTADO EN TIEMPO REAL

| Proyecto | Estado | Entorno | Notas |
|----------|--------|---------|-------|
| 🦅 **Sniper Bear** | 🟢 **Foco Único** | **WSL Nativo (Operativo)** | **BREAKTHROUGH:** Con data de Abril el bot rinde +155%. Se requiere Kill Switch 1m para evitar DD del 60% por liquidaciones. |
| 🦊 **Volume Hunter** | ⏸️ Pausado | WSL Nativo | En pausa operacional hasta cerrar Sniper Bear. |
| 🔮 **Triple Mode** | ❌ Abortado | WSL Nativo | Confirmado el retorno a estrategias atómicas especialistas. |

---

## 🔴 BLOQUEOS Y HALLAZGOS CRÍTICOS (Sesión 2026-04-09)

1. **Recuperación de Datos (Abril 2024):**
   - Se logró la descarga limpia de Abril-Agosto 2024 via WSL nativo.
   - **Resultado Backtest:** +154.82% Profit Bruto. El bot tiene un edge real masivo (Trailing Stop acumulado de +700%).

2. **Veredicto "Kill Switch 1m":**
   - Sin el Kill Switch de 1 minuto, el bot sufre 23-25 liquidaciones plenas en mercados laterales/rebotes violentos (Julio 2024).
   - **Conclusión:** El timeframe de 1m es el "airbag" vital para operar futuros x5. No es opcional.

3. **Filtro Macro EMA200:**
   - Implementado en `ChacalSniper_Bear_No1m.py`. Redujo trades falsos pero no evita las liquidaciones de trades ya abiertos. El blindaje real debe ser en la salida (1m).

---

## 📋 PRÓXIMOS PASOS (PLAN DE ACCIÓN - Mañana)

1. **DNAs de Salida Anti-Liquidación:**
   - Ajustar Stoploss fijos por par (especialmente ADA y BNB) para que actúen ANTES de la liquidación de Binance.

2. **Re-activación y Optimización del Kill Switch 1m:**
   - Volver a la base estable `ChacalSniper_Bear44.py`.
   - Limpiar e integrar la lógica de 1m con el dataset nativo ya verificado.

3. **Validación Final:**
   - Correr backtest final con 1m activo buscando reducir el Drawdown del 60% a niveles institucionales (<25%).

---
*Para auditorías profundas, ver: `PROJECT_SNIPER_AWS/AUDITORIA_FILTROS_MACRO.md`*
