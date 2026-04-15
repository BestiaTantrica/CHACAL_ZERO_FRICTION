# 🛰️ HILO DE MONITOREO: CHACAL TRIFÁSICO (V4.0 - ELITE)

> **Referencia Base:** Hilo `121f4b8e-37dc-40f5-be29-0f7bbcfe2f16` (Backtest Masivo +527.8%)
> **Última Sincronización:** 2026-04-11 17:15

---

## 📈 1. LÍNEA BASE DE RENDIMIENTO (ELITE DUAL)

*Estos son los valores teóricos validados en el laboratorio que debemos defender en producción.*

| Métrica | Valor Objetivo | Estado Actual |
| :--- | :--- | :--- |
| **ROI Anual Estimado** | +527.8% | 🟢 En Línea |
| **Max Drawdown (Histórico)** | 22.3% | 🟢 0% (Inicio) |
| **WinRate Promedio** | > 68% | - |
| **Capital Bajo Gestión** | 100% Rotativo | 🟢 OK |

---

## 🧭 2. ESTADO DEL RÉGIMEN ACTUAL (BTC)

> **Gatillo de Cambio:** ±4.3% Desviación EMA50 (1h)

- **Precio BTC:** $74,178.5 (Auditado)
- **EMA50 (1h):** ~$73,546.0 (Calc.)
- **Desviación:** 0.86%
- **BOT ACTIVO:** 🦅 **SNIPER BEAR V5** (Short-only)

---

## 📝 3. LOG DINÁMICO (CONDENSADO)

### [2026-04-14 23:25] - AUDITORÍA DE RUTINA (PEGASO)

- **Evento:** Verificación de racha sin trades.
- **Hallazgo 1:** Se detectaron 3 trades recientes (BTC, DOGE, XRP), todos SHORTS.
- **Hallazgo 2:** El sistema cambió de BULL a BEAR hoy a las 16:09 UTC.
- **Hallazgo 3:** El Bot Bull (Volume Hunter) fue detenido con 2 órdenes activas (Simuladas) al cambiar el régimen.
- **Diagnóstico:** El sistema está en el "Gap de Largos" (0% a 4.3% sobre EMA50). En este rango, el orquestador mantiene el Sniper Bear (Short-only), ignorando las subidas lentas.
- **Estado:** Operativo al 100%. Salud del servidor óptima (Swap 4GB OK).

---

## 🛠️ 4. ACCIONES DE MANTENIMIENTO REQUERIDAS

- [X] Ejecutar primer `status` en AWS. (PEGASO 2026-04-14)
- [ ] Evaluar reducción de `LATERAL_THRESHOLD` a 2.5% para activar Bull Hunter antes.
- [ ] Verificar sincronización de API Keys en Binance (Dry Run activo actualmente).

---

*Este hilo se condensará periódicamente moviendo los logs antiguos a una sección de 'Historial' para mantener la agilidad operativa.*
