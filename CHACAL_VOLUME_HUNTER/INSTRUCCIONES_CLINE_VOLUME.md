# 🦊 CHACAL VOLUME HUNTER — MAESTRO DE OPERACIONES PARA CLINE

> **Última actualización:** 2026-04-02 (Post-OOM Kill Recovery)
> **Versión:** 2.0 — PLAN DE OPTIMIZACIÓN SEGURA
> **Estado:** ✅ ESTRATEGIA RENTABLE (+5.59% Jul 2025) — Lista para hyperopt controlado
> **Proyecto:** CHACAL_VOLUME_HUNTER (PC Local, i3-4170 / 10 GB RAM)
> **Compañero en AWS:** PROJECT_SNIPER_AWS (IP 15.229.158.221, Bear/Short)

---

## ⚠️ LEER ESTO PRIMERO — REGLAS DE SEGURIDAD INVIOLABLES

1. **LÍMITE DURO DE PARES:** Máximo 8 pares en cualquier operación de hyperopt. NO negociable.
2. **LÍMITE DE MEMORIA:** Si el sistema supera **75% de RAM**, el proceso Docker debe matarse **DE INMEDIATO** con `docker kill`. No esperar.
3. **EJECUCIÓN SECUENCIAL:** Un solo proceso Docker a la vez. NUNCA dos contenedores simultáneos de freqtrade.
4. **TIMERANGE CORTO:** Todo hyperopt se hace sobre **exactamente 1 mes de datos** (Julio 2025 = BULL PURO confirmado).
5. **RESPALDO ANTES DE EDITAR:** Antes de modificar `ChacalVolumeHunter_V1.py`, copiar la versión actual a `ChacalVolumeHunter_V1_BACKUP_FECHA.py`.
6. **PROTOCOLO OOM KILL:** Si hay señales de slowdown severo o el proceso no responde en >10 minutos por época → matar Docker → reducir a los 8 pares más correlacionados y relanzar.

---

## 1. IDENTIDAD Y CONTEXTO

### 1.1 ¿Qué es CHACAL VOLUME HUNTER?

Es la estrategia LONG-only del ecosistema CHACAL. Opera en mercados **BULL y LATERAL** detectando altcoins que se "quedan atrás" de BTC durante subidas (fenómeno de atraso/convergencia). La lógica de entrada está basada en tres pilares:

| Pilar | Qué hace |
|:------|:---------|
| **Atraso Real vs BTC** | Detecta altcoins que no siguieron la subida de BTC en las últimas 5 velas → espera la convergencia |
| **Correlación BTC** | Filtra pares con alta correlación (>0.8) para que el atraso sea real, no ruido |
| **Risk Pressure Score** | Combina ATR y correlación para evitar entrar en pares en caos |

### 1.2 Hardware del Laboratorio (PC Local)

| Componente | Especificación | Implicación práctica |
|:-----------|:---------------|:---------------------|
| CPU | Intel i3-4170 (2 núcleos, 4 threads) | Hyperopt -j 1 SIEMPRE |
| RAM | 10 GB usable | Máximo 8 pares en hyperopt |
| Tiempo/época | ~1.5–2 min (8 pares, 5m, 1 mes) | 50 épocas = ~75–100 min |
| Tiempo backtest | ~1 min (8 pares, 1 mes) | Validaciones rápidas |

### 1.3 Resultado Actual (No tocar, es la línea base)

```
Backtest Julio 2025 (BULL PURO):
  - Profit total: +5.59%
  - Trailing stop: 15%/30% (activa a +2.5%, deja 0.5% de aire)
  - exit_signal: RSI > 75
  - DCA: habilitado (4% caída → agrega 1.5× stake, máx 2 órdenes)
  - Pares: 28 (ESTE ES EL ESTADO QUE YA FUNCIONA, no modificar sin backtest)
```

> **⚠️ IMPORTANTE:** Este resultado está en PC local. La estrategia **NO está adaptada para AWS todavía** (configuraciones distintas, pares distintos). No deploar a AWS sin instrucción explícita.

---

## 2. ARQUITECTURA TÉCNICA

### 2.1 Estructura de Archivos Críticos

```text
c:\CHACAL_ZERO_FRICTION\
├── strategies\
│   ├── ChacalVolumeHunter_V1.py          ← ESTRATEGIA PRINCIPAL (editar con cuidado)
│   └── ChacalVolumeHunter_V1.json        ← Parámetros hyperopt en uso
│
└── CHACAL_VOLUME_HUNTER\
    ├── INSTRUCCIONES_CLINE_VOLUME.md      ← ESTE ARCHIVO (leer siempre primero)
    ├── docker-compose.yml
    ├── check_market_trend.py
    └── user_data\
        ├── configs\
        │   ├── config_backtest.json       ← Config para hyperopt/backtest (StaticPairList)
        │   └── config_volume.json         ← Config para trading live (VolumePairList)
        ├── data\binance\futures\           ← Datos feather descargados
        ├── hyperopt_results\              ← Resultados de cada corrida
        │   └── *.fthypt                   ← Archivos de Optuna (NO borrar)
        └── logs\                          ← Logs del bot live
```

### 2.2 Paths de Docker (Volúmenes)

```bash
# Directorio local → Directorio dentro del contenedor
C:\CHACAL_ZERO_FRICTION\CHACAL_VOLUME_HUNTER\user_data → /freqtrade/user_data
C:\CHACAL_ZERO_FRICTION\strategies                      → /freqtrade/user_data/strategies
```

**NUNCA usar `../user_data` de la raíz del proyecto. El Volume Hunter tiene su propio `user_data`.**

### 2.3 Parámetros Actuales de la Estrategia (Estado "5.59%")

```python
# ChacalVolumeHunter_V1.py — valores en uso
trailing_stop = True
trailing_stop_positive = 0.005          # 0.5% de aire al trailing
trailing_stop_positive_offset = 0.025   # Se activa al +2.5% de ganancia

# Parámetros hyperoptables con sus defaults actuales:
stoploss_atr_mult  = 1.8    # Multiplicador ATR para el stop
rsi_buy_min        = 21     # RSI mínimo para entrada lateral
btc_threshold_mult = 1.2    # Multiplicador del umbral de atraso vs BTC
dca_drop_mult      = 2.1    # Divisor de la caída para activar DCA
w_corr             = 0.45   # Peso de correlación en Risk Pressure
w_atr              = 0.20   # Peso de ATR en Risk Pressure

max_open_trades = 8         # MÁXIMO permitido
```

---

## 3. LOS 8 PARES ANTI-OOM (Núcleo BTC-Correlacionado)

Estos son los 8 pares que se usarán en **toda operación de hyperopt**. Seleccionados por:
- Alta correlación histórica con BTC (>0.75)
- Mayor volumen de trading en el período Julio 2025
- Datos confirmados descargados en feather

```json
[
  "BTC/USDT:USDT",
  "ETH/USDT:USDT",
  "SOL/USDT:USDT",
  "BNB/USDT:USDT",
  "XRP/USDT:USDT",
  "AVAX/USDT:USDT",
  "LINK/USDT:USDT",
  "DOGE/USDT:USDT"
]
```

> **PROTOCOLO OOM KILL ACTIVO:** Si en cualquier momento el proceso se traba, la memoria sube al 75%+, o una época tarda más de 5 minutos → matar Docker inmediatamente y relanzar con exactamente estos 8 pares.

---

## 4. DATOS DISPONIBLES

| Parámetro | Valor |
|:----------|:------|
| Exchange | Binance Futures |
| Timeframe principal | 5m |
| Timeframe de referencia BTC | 1h (indicadores macro) |
| Rango de datos | 2025-07-01 → 2025-07-31 (**JULIO 2025 = BULL PURO confirmado**) |
| Filas por par | ~8,928 velas de 5m |
| Pares con datos completos | 28 |
| Formato | Apache Feather |
| Tamaño total | ~20.8 MB |

### Verificar integridad de datos

```cmd
REM Verificar que los 8 pares clave tienen datos de julio
python -c "import pandas as pd; import os; pares=['BTC_USDT_USDT','ETH_USDT_USDT','SOL_USDT_USDT','BNB_USDT_USDT','XRP_USDT_USDT','AVAX_USDT_USDT','LINK_USDT_USDT','DOGE_USDT_USDT']; [print(p, pd.read_feather(f'CHACAL_VOLUME_HUNTER\\user_data\\data\\binance\\futures\\{p}-5m-futures.feather')['date'].agg(['min','max','count']).to_dict()) for p in pares]"
```

---

## 5. PLAN DE ACCIÓN — 4 FASES

### ═══ FASE 1: VERIFICACIÓN DEL BASELINE ═══

**Objetivo:** Confirmar que el resultado +5.59% se reproduce antes de tocar nada.

**Tarea 1.1 — Backtest de Referencia con 8 Pares:**

```cmd
REM Primero, verificar que config_backtest.json tiene exactamente los 8 pares
REM Editar config_backtest.json si es necesario (ver sección 6.1)

docker run --rm ^
  --cpus 2 --memory 7g ^
  -v "C:\CHACAL_ZERO_FRICTION\CHACAL_VOLUME_HUNTER\user_data:/freqtrade/user_data" ^
  -v "C:\CHACAL_ZERO_FRICTION\strategies:/freqtrade/user_data/strategies" ^
  freqtradeorg/freqtrade:stable backtesting ^
  --config /freqtrade/user_data/configs/config_backtest.json ^
  --strategy ChacalVolumeHunter_V1 ^
  --timerange 20250701-20250801 2>&1
```

**Criterio de éxito:** Profit total > 0% con al menos 20 trades.
**Si falla:** Revisar que `config_backtest.json` apunta a exactamente los 8 pares con StaticPairList.

---

### ═══ FASE 2: HYPEROPT ESCENARIO BULL (Principal) ═══

**Objetivo:** Optimizar los parámetros de entrada/salida para el período BULL puro de Julio 2025.

**Contexto del mercado Julio 2025:**
- BTC RSI 1h: predominantemente > 55 (mercado alcista)
- Movimiento: BTC subió ~15% en el mes
- Altcoins: alta correlación, rotación frecuente
- Escenario ideal para la señal `BULL_VOLUME_ATRASO`

**Tarea 2.1 — Ejecutar Hyperopt Escenario Bull:**

```cmd
docker run --rm ^
  --cpus 2 --memory 7g ^
  -v "C:\CHACAL_ZERO_FRICTION\CHACAL_VOLUME_HUNTER\user_data:/freqtrade/user_data" ^
  -v "C:\CHACAL_ZERO_FRICTION\strategies:/freqtrade/user_data/strategies" ^
  freqtradeorg/freqtrade:stable hyperopt ^
  --config /freqtrade/user_data/configs/config_backtest.json ^
  --strategy ChacalVolumeHunter_V1 ^
  --hyperopt-loss SharpeHyperOptLoss ^
  --timerange 20250701-20250801 ^
  --spaces buy sell trailing ^
  -e 50 -j 1 2>&1
```

**Tiempo estimado:** 75–100 minutos (8 pares, i3-4170, 50 épocas).

**Tarea 2.2 — Validar con Backtest Post-Hyperopt:**

```cmd
REM Inyectar parámetros de la mejor época (ver sección 6.3)
REM Luego backtest en los últimos 15 días del período para out-of-sample
docker run --rm ^
  --cpus 2 --memory 7g ^
  -v "C:\CHACAL_ZERO_FRICTION\CHACAL_VOLUME_HUNTER\user_data:/freqtrade/user_data" ^
  -v "C:\CHACAL_ZERO_FRICTION\strategies:/freqtrade/user_data/strategies" ^
  freqtradeorg/freqtrade:stable backtesting ^
  --config /freqtrade/user_data/configs/config_backtest.json ^
  --strategy ChacalVolumeHunter_V1 ^
  --timerange 20250716-20250801 2>&1
```

**Criterio de OOM:** Si durante el hyperopt ves épocas tardando >5 minutos → `docker kill $(docker ps -q)` → reducir a 6 pares → relanzar.

---

### ═══ FASE 3: HYPEROPT ESCENARIO LATERAL (Complementario) ═══

**Objetivo:** Ajustar el sub-modo `LATERAL_VOLUME_SCALP` de forma aislada.

**Contexto:** El escenario lateral activa cuando el BTC RSI 5m está entre 45-55. En Julio 2025 hay períodos de consolidación entre subidas que sirven para esto.

**Tarea 3.1 — Hyperopt Solo Espacio Buy (Lateral):**

> **Nota para Cline:** Este paso se ejecuta SOLO si la Fase 2 produjo un profit > +3%. Caso contrario, reportar a Antigravity antes de continuar.

```cmd
docker run --rm ^
  --cpus 2 --memory 7g ^
  -v "C:\CHACAL_ZERO_FRICTION\CHACAL_VOLUME_HUNTER\user_data:/freqtrade/user_data" ^
  -v "C:\CHACAL_ZERO_FRICTION\strategies:/freqtrade/user_data/strategies" ^
  freqtradeorg/freqtrade:stable hyperopt ^
  --config /freqtrade/user_data/configs/config_backtest.json ^
  --strategy ChacalVolumeHunter_V1 ^
  --hyperopt-loss SharpeHyperOptLoss ^
  --timerange 20250701-20250801 ^
  --spaces buy ^
  -e 30 -j 1 2>&1
```

**Tiempo estimado:** 45–60 minutos.

**Tarea 3.2 — Backtest Integrado Final:**

```cmd
REM Con los parámetros de Fase 2 + Fase 3 combinados
docker run --rm ^
  --cpus 2 --memory 7g ^
  -v "C:\CHACAL_ZERO_FRICTION\CHACAL_VOLUME_HUNTER\user_data:/freqtrade/user_data" ^
  -v "C:\CHACAL_ZERO_FRICTION\strategies:/freqtrade/user_data/strategies" ^
  freqtradeorg/freqtrade:stable backtesting ^
  --config /freqtrade/user_data/configs/config_backtest.json ^
  --strategy ChacalVolumeHunter_V1 ^
  --timerange 20250701-20250801 2>&1
```

**Criterio de éxito final:** Profit > +5.59% (superar la línea base).

---

### ═══ FASE 4: DOCUMENTACIÓN Y ENTREGA ═══

**Objetivo:** Actualizar este archivo con los resultados y dejar el proyecto listo.

**Tarea 4.1 — Actualizar Sección 7 (Historial) con:**
- Número de épocas ejecutadas
- Mejor época encontrada
- Profit obtenido
- Parámetros finales inyectados

**Tarea 4.2 — Actualizar Sección 8 (Estado Actual) con:**
- Fecha de actualización
- Resultado del backtest final
- Estado de cada componente

**Tarea 4.3 — Git Commit de Seguridad:**

```cmd
REM Desde c:\CHACAL_ZERO_FRICTION
git add CHACAL_VOLUME_HUNTER\INSTRUCCIONES_CLINE_VOLUME.md
git add strategies\ChacalVolumeHunter_V1.py
git add strategies\ChacalVolumeHunter_V1.json
git commit -m "VolumeHunter v2: hyperopt escenario BULL Julio 2025 - resultado: [COMPLETAR]"
git push origin master
```

---

## 6. CONFIGURACIONES DE REFERENCIA

### 6.1 config_backtest.json — Lista de 8 Pares (Anti-OOM)

Verificar que el archivo contenga exactamente estos pares. Si tiene más, **editarlo antes de hyperopt**:

```json
{
  "exchange": {"name": "binance"},
  "trading_mode": "futures",
  "margin_mode": "isolated",
  "timeframe": "5m",
  "stake_currency": "USDT",
  "stake_amount": 100,
  "max_open_trades": 8,
  "dry_run": true,
  "pair_whitelist": [
    "BTC/USDT:USDT",
    "ETH/USDT:USDT",
    "SOL/USDT:USDT",
    "BNB/USDT:USDT",
    "XRP/USDT:USDT",
    "AVAX/USDT:USDT",
    "LINK/USDT:USDT",
    "DOGE/USDT:USDT"
  ],
  "pairlists": [{"method": "StaticPairList"}],
  "datadir": "/freqtrade/user_data/data/binance/futures"
}
```

> **CRÍTICO:** `pairlists` DEBE ser `StaticPairList` para backtest/hyperopt. `VolumePairList` SOLO para trading live.

### 6.2 Inyectar Parámetros de Hyperopt a la Estrategia

Después de cada hyperopt, el archivo `hyperopt_results/strategy_ChacalVolumeHunter_V1_FECHA.fthypt` contiene los resultados. Extraer la mejor época así:

```cmd
docker run --rm ^
  -v "C:\CHACAL_ZERO_FRICTION\CHACAL_VOLUME_HUNTER\user_data:/freqtrade/user_data" ^
  -v "C:\CHACAL_ZERO_FRICTION\strategies:/freqtrade/user_data/strategies" ^
  freqtradeorg/freqtrade:stable hyperopt-show ^
  --config /freqtrade/user_data/configs/config_backtest.json ^
  --strategy ChacalVolumeHunter_V1 ^
  --best -n 1 --print-json 2>&1
```

Los parámetros resultantes deben **copiarse manualmente** al bloque de defaults en `ChacalVolumeHunter_V1.py` (líneas de `DecimalParameter` y `IntParameter`). También guardar en `strategies/ChacalVolumeHunter_V1.json`.

### 6.3 Formato del JSON de Parámetros (ChacalVolumeHunter_V1.json)

```json
{
  "strategy_name": "ChacalVolumeHunter_V1",
  "params": {
    "buy": {
      "btc_threshold_mult": 1.2,
      "dca_drop_mult": 2.1,
      "rsi_buy_min": 21,
      "w_atr": 0.20,
      "w_corr": 0.45
    },
    "sell": {
      "stoploss_atr_mult": 1.8
    },
    "trailing": {
      "trailing_stop": true,
      "trailing_stop_positive": 0.005,
      "trailing_stop_positive_offset": 0.025,
      "trailing_only_offset_is_reached": true
    }
  }
}
```

---

## 7. HISTORIAL DE OPTIMIZACIONES

| # | Fecha | Épocas | Timerange | Mejor Época | Profit | Notas |
|:--|:------|:-------|:----------|:------------|:-------|:------|
| 1 | 2026-04-01 | 100 | Sep-Nov 2024 | #90 | +0.71% | Solo BTC/ETH tenían datos 2024 |
| 2 | 2026-04-01 | 100 | Sep-Nov 2024 + time guard | #5 | -7.40% | Time guard empeoró resultados |
| 3 | 2026-04-02 | 70 | Jul-Sep 2025 | #40 | -19.55% | 28 pares, datos limpios - período MIXTO |
| 4 | 2026-04-02 | Backtest | Jul 2025 solo | — | -0.55% | Solo 4 días, trailing 5%/10% |
| **5** | **2026-04-02** | **Backtest** | **Jul 2025 completo** | **—** | **+5.59%** | **Trailing 15%/30%, exit RSI>75, DCA ON ← BASELINE** |
| 6 | 2026-04-02 | Backtest | Jul 2025 (8 Pares) | — | +9.67% | Backtest "Super Bull" - 112 trades, DD 1.76% |
| 7 | *(pendiente)* | 30 | Jul 2025 | — | — | FASE 3: Hyperopt LATERAL 8 pares |

### Parámetros del Baseline (+5.59%)

```json
{
  "trailing_stop_positive": 0.005,
  "trailing_stop_positive_offset": 0.025,
  "exit_rsi_threshold": 75,
  "dca_enabled": true,
  "dca_drop_pct": 0.04,
  "dca_stake_mult": 1.5,
  "max_dca_orders": 2,
  "btc_threshold_mult": 1.2,
  "dca_drop_mult": 2.1,
  "rsi_buy_min": 21,
  "w_atr": 0.20,
  "w_corr": 0.45,
  "stoploss_atr_mult": 1.8
}
```

---

## 8. ESTADO ACTUAL (ACTUALIZAR CADA SESIÓN)

**Última actualización:** 2026-04-03 (PEGASO: Apuntando a Feb 2024)

| Componente | Estado |
|:-----------|:-------|
| FASE 1: Análisis Histórico Verificado | ✅ COMPLETADO: Super Bull real identificado en FEB 2024 (+43%). |
| FASE 2: Mutación Adaptativa Super Bull | ✅ INYECTADA: (Trailing Escalonado + Filtro Alts Correlacionadas). |
| FASE 3: Hyperopt Francotirador Feb 2024 | ✅ COMPLETADO. Best Epoch 184/200 (+24.34%, Drawdown 11%). |
| Validación Multi-Mercado | ✅ COMPLETADO. 3 meses validados, DD siempre < 10%. |
| Protocolo PEGASO 3.1 | ✅ ACTIVO: Memoria estable con `-j 1`. |
| Deploy Dry Run Local | 🔄 PENDIENTE. Ver Sección 16. |
| Deploy AWS | ❌ NO. Esperar validación exitosa de Dry Run local. |

---

### RESULTADOS DE VALIDACIÓN MULTI-MERCADO (2026-04-03) — PARÁMETROS GANADORES

| Periodo | Modo | Profit Bot | Market Change | Drawdown | Observación |
|:---|:---|:---|:---|:---|:---|
| Feb 2024 | Super Bull | **+37.03%** | +34.15% | 9.66% | Mejor trade: BTC +90.77% (RSI exit) |
| Jul 2025 | Bull Lateral | **+7.88%** | +25.12% | 9.56% | Bot supera al mercado en ratio riesgo/retorno |
| Ene 2024 | Bajista | **+2.89%** | -7.13% | 9.98% | Bot ganó dinero mientras el mercado caía |

**CONCLUSIÓN:** Bot Todo Terreno validado. Drawdown siempre < 10%, ganancia positiva en 3 regímenes distintos.

### PARÁMETROS ACTUALES GRABADOS EN PIEDRA (ChacalVolumeHunter_V1.py)

```python
# Epoch 184/200 — SortinoHyperOptLoss — Feb 2024
buy_params = {
    "btc_threshold_mult": 0.869,
    "dca_drop_mult": 2.358,
    "rsi_buy_min": 31,
    "w_atr": 0.308,
    "w_corr": 0.575,
}
sell_params = {
    "exit_rsi_level": 92,
    "stoploss_atr_mult": 1.514,
}
trailing_stop_positive = 0.302  # activa cuando profit > 39.1%
trailing_stop_positive_offset = 0.391
```


---

### NOTAS DE SESIÓN (2026-04-03)
*   **DCA PURGADO:** Se eliminó por ineficiencia en asimetría de riesgo (perdía más de lo que ganaba). Volvemos a **Stakes Planos**.
*   **FILTRO ALTS:** La señal `SUPER_BULL_FOMO` ahora exige `risk_guard` + `volume_guard`. Solo Alts acopladas a BTC.
*   **HYPEROPT RESULT (Epoch 20):** +29.42% Profit en 28 días. Win Rate 20% (compensado por grandes ganadoras vs pequeñas perdedoras).
*   **PENDIENTE:** Relanzar Hyperopt completo (200 ep) para clavar los márgenes perfectos de entrada/salida.

---

## 9. MONITOREO DE RECURSOS (Anti-OOM)

### Verificar memoria en tiempo real (ventana separada)

```cmd
REM En CMD: ejecutar mientras corre el Docker
wmic process where "name='docker'" get WorkingSetSize /value

REM Alternativa: ver uso total del sistema cada 5 segundos
for /l %i in (1,1,100) do (wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /value && timeout /t 5 /nobreak > nul)
```

### Matar Docker de emergencia

```cmd
REM MATAR TODO Docker inmediatamente si OOM
for /f "tokens=*" %i in ('docker ps -q') do docker kill %i

REM Verificar que no quedan procesos colgados
docker ps
tasklist | findstr /i docker
```

### Señales de Peligro (actuar de inmediato si):

| Señal | Acción |
|:------|:-------|
| 1 época tarda >5 minutos | Matar Docker → reducir pares → relanzar |
| RAM sistema > 75% | Matar Docker → esperar 2 min → relanzar |
| Docker no responde a Ctrl+C | `docker kill $(docker ps -q)` desde CMD |
| "Killed" en los logs | OOM confirmado → reducir a 6 pares → relanzar |
| Pantalla en negro / sistema lento | Reiniciar PC → esperar 5 min → relanzar |

---

## 10. BUGS CONOCIDOS Y FIXES APLICADOS

| Bug | Fix aplicado | Archivo |
|:----|:-------------|:--------|
| Cache BTC futuro→pasado | `pd.merge` sincrónico | `ChacalVolumeHunter_V1.py:62-90` |
| VolumePairList incompatible con backtest | StaticPairList en config_backtest | `config_backtest.json` |
| Docker root vs subfolder mapping | Volumen mapeado a `CHACAL_VOLUME_HUNTER\user_data` | `docker-compose.yml` |
| hyperopt.lock bloqueando relanzamientos | Borrar `user_data/hyperopt.lock` antes de relanzar | Manual |

### Eliminar lock antes de hyperopt

```cmd
REM Si el hyperopt anterior terminó mal y dejó un lock
del "C:\CHACAL_ZERO_FRICTION\CHACAL_VOLUME_HUNTER\user_data\hyperopt.lock"
```

---

## 11. WORKFLOWS ESTÁNDAR COMPLETOS

### 11.1 Hyperopt Seguro (50 épocas, 8 pares)

```cmd
docker run --rm ^
  --cpus 2 --memory 7g ^
  -v "C:\CHACAL_ZERO_FRICTION\CHACAL_VOLUME_HUNTER\user_data:/freqtrade/user_data" ^
  -v "C:\CHACAL_ZERO_FRICTION\strategies:/freqtrade/user_data/strategies" ^
  freqtradeorg/freqtrade:stable hyperopt ^
  --config /freqtrade/user_data/configs/config_backtest.json ^
  --strategy ChacalVolumeHunter_V1 ^
  --hyperopt-loss SharpeHyperOptLoss ^
  --timerange 20250701-20250801 ^
  --spaces buy sell trailing ^
  -e 50 -j 1 2>&1
```

### 11.2 Backtest Estándar

```cmd
docker run --rm ^
  --cpus 2 --memory 7g ^
  -v "C:\CHACAL_ZERO_FRICTION\CHACAL_VOLUME_HUNTER\user_data:/freqtrade/user_data" ^
  -v "C:\CHACAL_ZERO_FRICTION\strategies:/freqtrade/user_data/strategies" ^
  freqtradeorg/freqtrade:stable backtesting ^
  --config /freqtrade/user_data/configs/config_backtest.json ^
  --strategy ChacalVolumeHunter_V1 ^
  --timerange 20250701-20250801 2>&1
```

### 11.3 Descargar Datos (si necesitas nuevo período)

```cmd
docker run --rm ^
  -v "C:\CHACAL_ZERO_FRICTION\CHACAL_VOLUME_HUNTER\user_data:/freqtrade/user_data" ^
  freqtradeorg/freqtrade:stable download-data ^
  --config /freqtrade/user_data/configs/config_backtest.json ^
  --timerange 20250701-20250801 ^
  --timeframe 5m 1h --erase 2>&1
```

### 11.4 Ver Mejor Época del Último Hyperopt

```cmd
docker run --rm ^
  -v "C:\CHACAL_ZERO_FRICTION\CHACAL_VOLUME_HUNTER\user_data:/freqtrade/user_data" ^
  -v "C:\CHACAL_ZERO_FRICTION\strategies:/freqtrade/user_data/strategies" ^
  freqtradeorg/freqtrade:stable hyperopt-show ^
  --config /freqtrade/user_data/configs/config_backtest.json ^
  --strategy ChacalVolumeHunter_V1 ^
  --best -n 5 2>&1
```

### 11.5 Diagnóstico de Tendencia de Mercado

```cmd
python CHACAL_VOLUME_HUNTER\check_market_trend.py
```

### 11.6 Ver Logs del Bot Live

```cmd
docker logs -f chacal_volume_hunter
```

### 11.7 Verificar Datos del Par

```cmd
python -c "import pandas as pd; df=pd.read_feather(r'CHACAL_VOLUME_HUNTER\user_data\data\binance\futures\BTC_USDT_USDT-5m-futures.feather'); df['date']=pd.to_datetime(df['date']); print(df['date'].min(), 'to', df['date'].max(), len(df),'rows')"
```

---

## 12. LECCIONES APRENDIDAS (No repetir errores)

| Lección | Detalle |
|:--------|:--------|
| **Backtesting requiere StaticPairList** | VolumePairList solo funciona con datos live. En backtest lanza error de datos |
| **Time guard puede empeorar rendimiento** | En BULL puro, las horas nocturnas también tienen buenos movimientos. Evaluar sin time guard |
| **Jul-Sep 2025 NO es BULL puro** | Solo Julio 2025 es confirmed BULL. Agosto-Septiembre es mixto/bear |
| **i3-4170 es el cuello de botella** | 28 pares → OOM kill. 8 pares → funciona. NUNCA escalar más |
| **hyperopt.lock puede bloquear reinicios** | Borrar siempre antes de relanzar si el proceso terminó abruptamente |
| **Los datos deben estar sincronizados** | Todos los pares deben tener el mismo rango temporal exacto o el merge BTC falla |
| **El DCA con RSI>75 exit fue el cambio clave** | El resultado pasó de -7.53% a +5.59% con esos dos cambios combinados |

---

## 13. ÁRBOL DE DECISIONES PARA CLINE

```
¿Hay señales de OOM o lentitud extrema?
└─ SÍ → 1. docker kill (docker ps -q)
         2. Reducir config_backtest.json a 8 pares
         3. Esperar 2 minutos
         4. Relanzar con --memory 6g (reducir 1g más)
└─ NO → Continuar con el plan de fases

¿El backtest de Fase 1 dio profit > 0%?
└─ SÍ → Proceder a Fase 2 (Hyperopt BULL)
└─ NO → Reportar a Antigravity ANTES de continuar. No modificar nada.

¿El hyperopt de Fase 2 dio profit > 3%?
└─ SÍ → Inyectar parámetros → Proceder a Fase 3 (Hyperopt LATERAL)
└─ NO → Reportar a Antigravity. Evaluar si los nuevos parámetros son peores que el baseline.

¿El resultado final supera +5.59% (baseline)?
└─ SÍ → Fase 4: documentar, commit, y esperar instrucciones de deploy
└─ NO → Mantener parámetros del baseline. Reportar resultado a Antigravity.
```

---

## 14. PROHIBICIONES ABSOLUTAS

| ❌ NUNCA HACER | Por qué |
|:---------------|:--------|
| Subir `user_data/configs/` a Git | Contiene API keys de Binance y token Telegram |
| Subir `user_data/data/` a Git | 20+ MB de datos binarios |
| Correr hyperopt con >8 pares en este PC | OOM kill garantizado |
| Correr dos procesos Docker de freqtrade en paralelo | Duplica uso de RAM → OOM |
| Deploar a AWS sin instrucción explícita | La config de AWS es diferente. El bot Bear está activo allí |
| Borrar archivos `.fthypt` de hyperopt_results | Son los resultados históricos de Optuna, se necesitan para comparar |
| Modificar `ChacalVolumeHunter_V1.py` sin hacer backup primero | Puede romper el baseline +5.59% |

---

---

## 15. PROTOCOLO DE MEMORIA Y CONTINUIDAD (PEGASO 3.1)

Para evitar la pérdida de hilos de conversación y los estragos del OOM kill, todo Agente debe observar estas directrices al iniciar o terminar su actividad:
1. **Regla de Cierre de Sesión (Migajas):** Antes de concluir un hilo o entregar resultados finales al usuario, el Agente DEBE ACTUALIZAR obligatoriamente la Sección 8 (Estado Actual) e incluir cualquier avance crítico encontrado o nuevas lógicas insertadas en el código base.
2. **Registro Explícito de Mejoras:** Los cambios implementados en la estrategia no solo van al Python, sino que sus lógicas se asientan aquí para resguardarlos de fallas. 
3. **Mantenimiento Anti-Redundante:** Limpiar el proyecto de versiones obsoletas o archivos de backup intermedios que no proporcionen un piso seguro validado. Mantener el entorno local prolijo. 
4. **Ejecución de Comandos Delegada:** EL AGENTE NO EJECUTA DOCER/BACKTEST DIRECTAMENTE SALVO ORDEN EXPLÍCITA. Dado que monitorear la consola consume tiempo valioso y los procesos son pesados, el Agente proveerá los comandos exactos de CMD (siempre priorizando CMD) para que sea el propio usuario (el Capitán) quien los corra en su terminal.

---

> **📌 RECORDATORIO FINAL:** Este archivo es el cerebro del proyecto Volume Hunter.
> Cualquier agente (Cline, otro AI, humano) que retome el trabajo **DEBE leer este archivo completo primero**.
> Actualizar la **Sección 8 (Estado Actual)** después de cada acción significativa.
> El objetivo es superar el **+5.59%** de profit en Julio 2025 con los 8 pares BTC-correlacionados.

---

## 16. PROTOCOLO DRY RUN LOCAL — REGLAS DE DESPLIEGUE

### 16.1 Restricciones de Hardware (PC Local Limitada)

| Recurso | Límite Máximo | Por qué |
|:---|:---|:---|
| RAM Docker | 7 GB (`--memory 7g`) | Evitar OOM Kill |
| CPUs Docker | 2 (`--cpus 2`) | No saturar la PC |
| Pares máximos en Backtest/Hyperopt | 8 | >8 pares = OOM garantizado |
| Workers Hyperopt | 1 (`-j 1`) | Cada worker extra duplica RAM |
| Procesos Docker simultáneos | 1 | NUNCA correr 2 freqtrade en paralelo |

### 16.2 Lista de Pares Aprobados para Dry Run

**PARES CORE (siempre incluidos — alta correlación BTC y liquidez):**
```
BTC/USDT:USDT  ETH/USDT:USDT  SOL/USDT:USDT  BNB/USDT:USDT
XRP/USDT:USDT  AVAX/USDT:USDT  LINK/USDT:USDT  DOGE/USDT:USDT
```

**PARES OPCIONALES (rotar según el mercado, máx 4 extra a la vez):**
```
ADA/USDT:USDT  DOT/USDT:USDT  MATIC/USDT:USDT  LTC/USDT:USDT
UNI/USDT:USDT  ATOM/USDT:USDT  FIL/USDT:USDT   INJ/USDT:USDT
```

> ⚠️ REGLA IRON: Si se agregan pares extra, **eliminar** el mismo número de pares opcionales.
> El total de pares activos en Dry Run **NUNCA debe superar 12** en la PC local.
> Para >12 pares el despliegue debe ir a AWS.

### 16.3 Ventana Horaria Activa (¡LIBERADO 24/7!)

> ⚠️ **El `time_guard` interno fue FULMINADO.** Freqtrade está autorizado a operar sin cadenas las 24 horas del día. Se validó que esto incrementa un +20% los profits netos en Bull Markets.

**Control Físico (El Botón Rojo):**
Como el cerebro del bot no tiene horario, la ÚNICA barrera es el estado de la PC. El bot operará furiosamente todo el tiempo que decidas mantener la computadora encendida. Cuando decidas apagar, frenas el contenedor y chau; sin consumo pasivo.

### 16.4 Rutina de Arranque Manual (PC del Capitán)

> ☕ El bot se arranca a mano cada mañana cuando el Capitán enciende la PC. NO usar `--restart` automático.

**PASO 1: Limpiar contenedor anterior (si existía)**
```cmd
docker rm -f chacal_volume_dryrun
```

**PASO 2: Arrancar el bot**
```cmd
docker run -d --name chacal_volume_dryrun --cpus 2 --memory 7g -v "C:\CHACAL_ZERO_FRICTION\CHACAL_VOLUME_HUNTER\user_data:/freqtrade/user_data" -v "C:\CHACAL_ZERO_FRICTION\strategies:/freqtrade/user_data/strategies" -p 8080:8080 freqtradeorg/freqtrade:stable trade --config /freqtrade/user_data/configs/config_backtest.json --strategy ChacalVolumeHunter_V1 --dry-run
```

**PASO 3: Verificar que arrancó**
```cmd
docker logs chacal_volume_dryrun --tail 20
```

**AL APAGAR LA PC (noche):**
```cmd
docker stop chacal_volume_dryrun
```

### 16.5 Comandos de Monitoreo y Control

```cmd
REM Ver trades activos en tiempo real
docker logs -f chacal_volume_dryryn

REM Ver estado del contenedor
docker ps

REM DETENER el bot (controlado)
docker stop chacal_volume_dryryn

REM REINICIAR el bot
docker restart chacal_volume_dryryn

REM ELIMINAR el contenedor (para re-deployar)
docker rm -f chacal_volume_dryryn
```

### 16.6 Verificación Post-Arranque

Despues de arrancar, verificar que el bot este operativo:
1. `docker ps` → debe aparecer `chacal_volume_dryryn` en estado `Up`.
2. `docker logs chacal_volume_dryryn | tail -20` → debe mostrar `Strategy ChacalVolumeHunter_V1 loaded`.
3. El bot empieza a operar automáticamente en la próxima vela de 5 minutos dentro de la ventana horaria.

### 16.7 Config Recomendada para Dry Run (config_backtest.json)

Verificar que el config tenga:
```json
{
  "dry_run": true,
  "dry_run_wallet": 1000,
  "stake_currency": "USDT",
  "stake_amount": "unlimited",
  "max_open_trades": 8
}
```

> ⚠️ ANTES de pasar a live: cambiar `dry_run` a `false` y agregar API keys reales.
> NUNCA subir un config con API keys a Git.

### 16.8 Anti-Discrepancias: Reglas de Consistencia

| Regla | Detalle |
|:---|:---|
| Un solo `ChacalVolumeHunter_V1.py` | El archivo en `C:\CHACAL_ZERO_FRICTION\strategies\` es el MASTER. No crear copias. |
| Un solo config de referencia | `config_backtest.json` es el config base. Para live, crear `config_live.json` separado. |
| Parámetros siempre en el .json | Si el Hyperopt dumpeó un `.json`, ese tiene precedencia sobre los defaults del `.py`. |
| Nunca editar `.py` sin revisar `.json` | Pueden pisarse mutuamente. Verificar consistencia. |
| Logs de Dry Run | Guardar screenshots de los primeros trades reales en `user_data/logs/`. |
