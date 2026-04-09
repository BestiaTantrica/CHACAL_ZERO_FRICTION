# PLAN DE ALINEACIÓN — TRIPLEMODE SIN PISADAS

## 1) Congelar entorno (obligatorio)

1. Matar procesos viejos:
   ```cmd
   wsl -d Ubuntu -- bash -lc "pkill -f 'freqtrade.*(backtesting|hyperopt)' || true"
   ```
2. Verificar que estrategias activas están en `shared/strategies`.
3. NO mezclar corridas en paralelo.

## 2) Config limpio para selector (sin override global de stoploss)

- Usar: `projects/bear/user_data/configs/config_backtest_selector_clean.json`
- Regla: no incluir `"stoploss": -0.99` en config cuando se audita selector.

## 3) Política de JSON (evitar contaminación)

1. Backup de JSON activo antes de cada ensayo:
   - `ChacalTripleMode_CONTAMINADO_YYYYMMDD_HHMMSS.json`
   - `ChacalSniper_Bear_ULTRA_CONTAMINADO_YYYYMMDD_HHMMSS.json`
2. Si un hyperopt da malos resultados, **no exportar ese JSON como activo**.
3. Confirmar en logs:
   - `Loading parameters from file ...`
   - y que el stoploss mostrado sea el esperado para la prueba.

## 4) Protocolo de validación por capas (orden correcto)

### Capa A — Sanidad de runtime
- Smoke test corto (1-2 días) para ULTRA y TripleMode.
- Debe no haber `NameError`, ni mezclas de procesos.

### Capa B — Validación de modo individual
- Primero validar comportamiento por tags (`SUPER_BEAR`, `BEAR_NORMAL`, `LATERAL_BEAR`).
- Si `LATERAL_BEAR` casi no entra, no optimizar global todavía: corregir selector/reglas de entrada.

### Capa C — Integración automática
- Recién cuando los bloques por modo estén validados, correr ventana global.

## 5) Matriz mínima recomendada

1. `20240801-20240810` (super bear)
2. `20240901-20241001` (lateral bear) — solo cuando existan datos 1m/5m completos
3. `20240401-20240901` (global) — solo con cobertura completa

## 6) Criterio de Promote/Rollback

- Promote TripleMode solo si:
  - mejora profit en >= 2/3 ventanas,
  - no empeora drawdown de forma material,
  - y mejora distribución de tags (lateral realmente protege).
- Si no cumple: rollback a ULTRA baseline y TripleMode queda en laboratorio.

## 7) Comandos de verificación rápida

```cmd
wsl -d Ubuntu -- bash -lc "cd /home/chacal/chacal_zero_friction && make backtest-bear TIMERANGE=20240801-20240810 BEAR_STRATEGY=ChacalTripleMode"
wsl -d Ubuntu -- bash -lc "cd /home/chacal/chacal_zero_friction && make backtest-bear TIMERANGE=20240801-20240810 BEAR_STRATEGY=ChacalSniper_Bear_ULTRA"
wsl -d Ubuntu -- bash -lc "cd /home/chacal/chacal_zero_friction && make list-data-bear"
```
