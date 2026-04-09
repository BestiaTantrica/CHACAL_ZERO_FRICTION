# 🦅 ÓRDENES PARA CLINE: REFUERZO SNIPER BEAR

> **Misión:** Blindar `ChacalSniper_Bear44.py` contra liquidaciones y reactivar el Airbag de 1m.
> **Contexto:** El bot tiene un edge de +155%, pero muere en laterales por falta de resolución temporal (1m) y stoploss laxos.

---

## 🧹 PASO 0: LIMPIEZA FINAL
Verificar y eliminar cualquier rastro de `TripleMode` que Antigravity haya omitido.
- `del PROJECT_SNIPER_AWS/user_data/strategies/ChacalTripleMode*`
- `del PROJECT_SNIPER_AWS/AUDITORIA_TRIPLEMODE.md`

---

## 🛠️ PASO 1: ENDURECIMIENTO DE STOPLOSS (ADN)
Modificar `PROJECT_SNIPER_AWS/user_data/strategies/ChacalSniper_Bear44.py`:

1.  **Vincular `_sl_for_pair` al DNA:**
    ```python
    def _sl_for_pair(self, pair: str) -> float:
        # Priorizar el stoploss del DNA sobre el parámetro global
        dna_sl = self.hyperopt_dna.get(pair, {"bear_sl": -0.09})["bear_sl"]
        return dna_sl
    ```
2.  **Hardening ADA/BNB:**
    Asegurar que en `hyperopt_dna`, ADA no supere `-0.022` y BNB `-0.048`. Si el mercado se vuelve más agresivo, reducir un 10% adicional.

---

## ⚡ PASO 2: REACTIVACIÓN KILL SWITCH 1m
Implementar la salida rápida por RSI en 1 minuto para evitar "Trades Zombie".

1.  **Informative Pairs:** Añadir `("BTC/USDT:USDT", "1m")`.
2.  **Lógica 1m en `custom_exit`:**
    Si el trade lleva abierto > 1 hora y el `RSI_1m` cruza hacia arriba de `rsi_kill_switch`, cerrar inmediatamente.
    *(Esto evita quedarse atrapado en micro-rebotes que luego liquidan la cuenta x5).*

---

## 📈 PASO 3: VALIDACIÓN NATIVA (WSL)
Ejecutar el backtest sin Docker para máxima velocidad:
```bash
freqtrade backtesting --strategy ChacalSniper_Bear44 --timerange 20240401-20240831 --datadir user_data/data/binance/futures --timeframe 5m
```
**Métrica de Éxito:** Drawdown < 25% y Liquidaciones = 0.

---
**REM:** No complicar la lógica. Queremos ejecución institucional: entrada precisa, salida rápida.
