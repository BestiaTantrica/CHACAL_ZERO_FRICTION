# 📊 CHACAL MASTER ESTADO — TABLERO GLOBAL

> **Última actualización:** 2026-04-08
> **Estado:** Repo en saneamiento. Migración a WSL. Evidencias separadas.

---

## 🚦 ESTADO EN TIEMPO REAL

| Proyecto | Estado | Entorno | Notas |
|----------|--------|---------|-------|
| 🦅 **Sniper Bear** | 🟢 **Foco Único** | WSL Nativo | Edge confirmado (>101% profit). Dataset Abril bajado OK. Filtrado macro (EMA200) aplicado. Diagnóstico letal: apagar el Kill Switch de 1m provoca 60% Drawdown y +23 liquidaciones cruzadas. |
| 🦊 **Volume Hunter** | ⏸️ Pausado | WSL Nativo | En pausa hasta estabilizar la base Bear. |
| 🔮 **Triple Mode** | ❌ Abortado temporal. | WSL Nativo | Rollback por conflictos de selectores. |

---

## 🔴 BLOQUEOS Y HALLAZGOS CRÍTICOS

1. **El Edge de Abril Existe (Resolución):**
   - El entorno *WSL + Makefile* logró descargar los datos perfectos de Abril 2024.
   - El edge base aisladamente probó su vigencia: **Fase 2 arrojó +154.82% y Fase 3 (con filtro EMA200) arrojó +101.79%**.

2. **La Trampa de las Micro-velas (El 1m es Vida o Muerte):**
   - Al quitar el Kill Switch de `1m`, descubrimos que la estrategia sufre un **Drawdown de ~60% y +23 liquidaciones**.
   - **Conclusión Definitiva:** El bot es extremadamente rentable pero absolutamente dependiente de un stop de emergencia micro-scópico antes de que un pump cierre la vela de 5m con apalancamiento x5.

---

## 📋 PRÓXIMOS PASOS (PLAN DE ACCIÓN - PRÓXIMA SESIÓN)

1. **Ajuste del ADN Anti-Liquidación:**
   - Calibrar los hard-stoploss (Particularmente ADA y BNB) en la tabla base de `ChacalSniper_Bear44.py`.
   
2. **Re-activación y Tuneo del Kill Switch 1m:**
   - Volver a prender la condicional de escape basado en RSI de 1 minuto en el framework de la estrategia.

3. **Validación Definitiva (Prueba de Fuego):**
   - Correr Backtest final con Data limpia de Abril + Filtro Macro EMA200 + StopLoss estricto + Kill Switch activo. El objetivo es que el DD baje de 58% a <25%.
