# 🦅 CHACAL SNIPER BEAR — MANUAL OPERATIVO v2.0
## PROJECT_SNIPER_AWS | Servidor AWS São Paulo | Solo SHORT

> **Versión:** 2.0 — POST-AUTOPSIA AGOSTO 2024
> **Última actualización:** 2026-04-05
> **LEER TAMBIÉN:** `C:\CHACAL_ZERO_FRICTION\PEGASO_MASTER_PROMPT.md` (contexto global)

---

## ⚡ INICIO DE SESIÓN — CHECKLIST (30 segundos)

```
[ ] 1. ¿Qué versión está en AWS? (git log en server)
[ ] 2. ¿El container Bear está running? (docker ps)
[ ] 3. ¿Hay trades abiertos ahora mismo? (freqtrade status)
[ ] 4. ¿Git local está sincronizado? (git status)
[ ] 5. ¿Cuál es el objetivo específico de esta sesión?
```

**Si no sabes algo → verificar ANTES de tocar código.**

---

## 1. IDENTIDAD Y MISIÓN

| Atributo | Valor |
|----------|-------|
| **Qué hace** | Shorts futuros en mercado BEAR — BTC bajo EMA50 (1h) |
| **Cuándo opera** | Solo cuando Master Bear Switch = ON (BTC bajista + ATR expandido) |
| **Entorno** | AWS `ec2-user@15.229.158.221` — 24/7 continuo |
| **Apalancamiento** | x5 (fijo en estrategia) |
| **Pares** | 8 pares core BTC-correlacionados |
| **Timeframe** | 5m (señales) + 1h (macro BTC) + 1m (kill switch) |
| **Compañero** | Volume Hunter en PC Local (Bull/Long) |

**Filosofía:** El Sniper NO abre posiciones si el mercado no está claramente bajista. El Master Bear Switch es el guardián. Sin él, el bot se suicida en mercados laterales (-40% demostrado).

---

## 2. ARQUITECTURA TÉCNICA

### 2.1 Servidor AWS
| Parámetro | Valor |
|-----------|-------|
| IP | `15.229.158.221` |
| Usuario | `ec2-user` |
| Llave SSH | `C:\CHACAL_ZERO_FRICTION\skills\llave-sao-paulo.pem` |
| Path en server | `/home/ec2-user/freqtrade` |
| Container | `Chacal_Sniper_AWS_Env` |
| Compose | `PROJECT_SNIPER_AWS\docker-compose.yml` |

### 2.2 Archivos Críticos
```
PROJECT_SNIPER_AWS\
├── INSTRUCCIONES_CLINE_BEAR.md          ← ESTE ARCHIVO
├── docker-compose.yml                   ← Config Docker AWS
└── user_data\
    ├── strategies\
    │   ├── ChacalSniper_Bear_ULTRA.py   ← Versión activa (con bugs pendientes)
    │   └── ChacalSniper_Bear44.py       ← Versión estable (Época 46, producción)
    ├── configs\
    │   ├── config_aws.json              ← Config live AWS  ← ❌ NUNCA a Git
    │   └── config_backtest.json         ← Config para backtests locales
    └── data\binance\futures\            ← Datos descargados (no subir a Git)
```

### 2.3 Reglas de Seguridad
- ❌ **NUNCA subir** `user_data/configs/` a Git (tokens Telegram, claves Binance)
- ❌ **NUNCA subir** `skills/llave-sao-paulo.pem` a Git
- ❌ **NUNCA subir** `user_data/data/` a Git (datos binarios pesados)
- ✅ `.gitignore` bloquea estas carpetas — verificar que sigue activo

---

## 3. ESTRATEGIA: ChacalSniper_Bear_ULTRA / Bear44

### 3.1 Master Bear Switch (Guardián Principal)
```python
btc_trend_bear  = BTC_close < BTC_EMA(50, '1h')
btc_vol_active  = BTC_ATR > BTC_ATR_mean(24h)
master_bear_switch = btc_trend_bear AND btc_vol_active
```
- Switch **ON** → puede abrir shorts
- Switch **OFF** → NO abre nada (mercado lateral/alcista)
- **Stress test confirmado:** Sin switch = -40% en Jun/Jul 2024. Con switch = +118.1% en 5 meses.

### 3.2 Lógica de Entrada — Condiciones (TODAS deben cumplirse)
```
1. master_bear_switch == ON
2. Volumen > media 20 velas × volume_mult
3. Cambio precio < -0.1% (precio bajando activamente)
4. RSI < rsi_bear_thresh (momentum bajista)
5. RSI cayendo (rsi < rsi.shift(1))
6. Precio < Bollinger mid band (bajo presión)
7. ADX > adx_threshold (tendencia fuerte, no ruido)
```

### 3.3 Lógica de Salida

| Salida | Condición | Nota |
|--------|-----------|------|
| `bear_roi_hit` | Profit ≥ ROI del par (DNA × roi_base × 0.8) | Salida normal |
| `rsi_kill_switch_short` | RSI > rsi_kill_switch AND ADX > adx_threshold | Anti-rebote |
| `trailing_stop` | Activa a +2.5%, deja 1% de aire | Captura tendencia |
| `custom_stoploss` | DNA del par (bear_sl) o default -7.5% | Límite de pérdida |
| **`kill_switch_1m`** | RSI 1m > 90 OR tiempo > 48h en pérdida | ⚠️ REACTIVAR — evita zombies |

### 3.4 ADN por Par (Código Genético — Época 46)

| Par | v_factor | pulse_change | bear_roi | bear_sl | Notas |
|-----|----------|-------------|----------|---------|-------|
| BTC | 4.660 | 0.004 | 2.2% | -3.1% | Estable |
| ETH | 5.769 | 0.004 | 1.8% | -3.1% | Estable |
| SOL | 5.386 | 0.001 | 4.2% | -4.0% | OK |
| BNB | 3.378 | 0.003 | 1.1% | -4.8% | ⚠️ SL insuficiente en crash |
| XRP | 5.133 | 0.004 | 4.2% | -5.4% | OK |
| ADA | 3.408 | 0.005 | 4.2% | -2.2% | ⚠️ SL MUY bajo — revisar |
| AVAX | 5.692 | 0.005 | 1.0% | -5.3% | OK |
| LINK | 5.671 | 0.005 | 3.8% | -4.1% | OK |

> ⚠️ **ADA con -2.2% de SL es peligroso en crashes violentos.** Revisar antes de live.

### 3.5 Parámetros Activos (Época 46 — PRODUCCIÓN SEGURA)

```json
{
  "v_factor_mult": 1.323,
  "adx_threshold": 26,
  "rsi_bear_thresh": 30,
  "volume_mult": 1.44,
  "roi_base": 0.045,
  "rsi_kill_switch": 48,
  "bear_stoploss": -0.090
}
```

### 3.6 Config de Trading AWS
| Parámetro | Valor |
|-----------|-------|
| Trading Mode | Futures |
| Margin Mode | Isolated |
| Leverage | x5 (fijo en estrategia) |
| Max Open Trades | 8 |
| Stake | Unlimited (balance ratio) |
| Tradable Balance Ratio | 0.90 |
| Timeframe | 5m |

---

## 4. VERSIONES DE LA ESTRATEGIA

| Archivo | Estado | Descripción | Cuándo usar |
|---------|--------|-------------|-------------|
| `ChacalSniper_Bear44.py` | ✅ ESTABLE | Época 46 ADN Oro — probado, sin bugs | **Producción / Dry Run activo** |
| `ChacalSniper_Bear_ULTRA.py` | ⚠️ BUGS | Época 7 DNA — más agresivo pero defectuoso | Solo desarrollo — NO LIVE |

### Bugs conocidos en Bear_ULTRA (pendientes de fix)
1. **Trades Zombie** — Sin Kill Switch 1m activo, posiciones quedan abiertas 15-19 días
2. **Liquidaciones** — BNB y ADA llegaron a liquidación en crash Agosto 2024
3. **AttributeError `.value`** — Fijo en L128 (parámetros constantes que llamaban `.value`)

---

## 5. WORKFLOWS OPERATIVOS

### 5.1 Verificar Estado del Bot en AWS
```cmd
REM Ver contenedores activos
ssh -i skills\llave-sao-paulo.pem ec2-user@15.229.158.221 "docker ps"

REM Ver logs recientes
ssh -i skills\llave-sao-paulo.pem ec2-user@15.229.158.221 "docker logs --tail 50 Chacal_Sniper_AWS_Env"

REM Ver trades abiertos
ssh -i skills\llave-sao-paulo.pem ec2-user@15.229.158.221 "docker exec Chacal_Sniper_AWS_Env freqtrade status"

REM Ver balance
ssh -i skills\llave-sao-paulo.pem ec2-user@15.229.158.221 "docker exec Chacal_Sniper_AWS_Env freqtrade balance"
```

### 5.2 Deploy de Cambios en AWS (Flujo Completo)
```cmd
REM PASO 1 — Commitear cambios locales
git add PROJECT_SNIPER_AWS\
git commit -m "[Bear] descripción del cambio - YYYY-MM-DD"
git push origin master

REM PASO 2 — Pull en server y reinicio
ssh -i skills\llave-sao-paulo.pem ec2-user@15.229.158.221 "cd /home/ec2-user/freqtrade && git pull origin master && docker-compose down && docker-compose up -d"

REM PASO 3 — Verificar que arrancó
ssh -i skills\llave-sao-paulo.pem ec2-user@15.229.158.221 "docker logs --tail 30 Chacal_Sniper_AWS_Env"
```

### 5.3 Subir Config al Server (sin Git — secretos)
```cmd
scp -i skills\llave-sao-paulo.pem ^
  PROJECT_SNIPER_AWS\user_data\configs\config_aws.json ^
  ec2-user@15.229.158.221:/home/ec2-user/freqtrade/user_data/configs/
```

### 5.4 Reiniciar Bot en AWS
```cmd
ssh -i skills\llave-sao-paulo.pem ec2-user@15.229.158.221 ^
  "cd /home/ec2-user/freqtrade && docker-compose down && docker-compose up -d"
```

### 5.5 Verificar Git Sincronización (Local vs AWS)
```cmd
REM Ver estado local
git log --oneline -10
git status

REM Ver qué tiene el server
ssh -i skills\llave-sao-paulo.pem ec2-user@15.229.158.221 "cd /home/ec2-user/freqtrade && git log --oneline -5"
```

---

## 6. WORKFLOWS DE DESARROLLO (LOCAL)

### 6.1 Backtest Bear (Futuros) — Comando Correcto
```cmd
docker run --rm ^
  -v "C:\CHACAL_ZERO_FRICTION\PROJECT_SNIPER_AWS\user_data:/freqtrade/user_data" ^
  freqtradeorg/freqtrade:stable backtesting ^
  --config /freqtrade/user_data/configs/config_backtest.json ^
  --strategy ChacalSniper_Bear_ULTRA ^
  --timerange 20240801-20240901 ^
  --datadir /freqtrade/user_data/data/binance/futures ^
  --data-format json ^
  --exchange binance
```

> **⚠️ CRÍTICO:** Siempre usar `--datadir`, `--data-format json` y `--exchange binance` para futuros.
> Sin esto, Docker busca datos en el path incorrecto y da 0 trades sin error claro.

### 6.2 Verificar Datos Disponibles (HACER SIEMPRE PRIMERO)
```cmd
docker run --rm ^
  -v "C:\CHACAL_ZERO_FRICTION\PROJECT_SNIPER_AWS\user_data:/freqtrade/user_data" ^
  freqtradeorg/freqtrade:stable list-data ^
  --config /freqtrade/user_data/configs/config_backtest.json ^
  --datadir /freqtrade/user_data/data/binance/futures
```

### 6.3 Descargar Datos de un Período
```cmd
docker run --rm ^
  -v "C:\CHACAL_ZERO_FRICTION\PROJECT_SNIPER_AWS\user_data:/freqtrade/user_data" ^
  freqtradeorg/freqtrade:stable download-data ^
  --config /freqtrade/user_data/configs/config_backtest.json ^
  --timerange 20240801-20240901 ^
  --timeframe 5m 1h 1m ^
  --exchange binance ^
  --trading-mode futures
```

### 6.4 Hyperopt Bear
```cmd
docker run --rm ^
  -v "C:\CHACAL_ZERO_FRICTION\PROJECT_SNIPER_AWS\user_data:/freqtrade/user_data" ^
  freqtradeorg/freqtrade:stable hyperopt ^
  --config /freqtrade/user_data/configs/config_backtest.json ^
  --strategy ChacalSniper_Bear_ULTRA ^
  --hyperopt-loss SharpeHyperOptLoss ^
  --timerange 20240801-20240901 ^
  --datadir /freqtrade/user_data/data/binance/futures ^
  --data-format json ^
  --exchange binance ^
  --spaces buy sell ^
  -e 100 -j 1
```

### 6.5 Ver Mejor Época del Hyperopt
```cmd
docker run --rm ^
  -v "C:\CHACAL_ZERO_FICTION\PROJECT_SNIPER_AWS\user_data:/freqtrade/user_data" ^
  freqtradeorg/freqtrade:stable hyperopt-show ^
  --config /freqtrade/user_data/configs/config_backtest.json ^
  --strategy ChacalSniper_Bear_ULTRA ^
  --best -n 5 --print-json
```

---

## 7. ÁRBOL DE DECISIONES OPERATIVO

```
¿Quiero hacer backtest/hyperopt?
├─ PRIMERO: list-data → ¿tienen datos del período?
│   ├─ NO → download-data con timeframes 5m 1h 1m
│   └─ SÍ → continuar
├─ SEGUNDO: verificar config → trading_mode: "futures", margin_mode: "isolated"
├─ TERCERO: lanzar con --datadir, --data-format json, --exchange binance
└─ Si 0 trades → problema de datos o config, NO de estrategia

¿Quiero deployar cambio en AWS?
├─ ¿Está comiteado y pusheado? → NO → git add / commit / push primero
├─ git pull en server → docker-compose down && up -d
└─ Verificar logs 30 seg después

¿El backtest dio resultado extraño (<10% del esperado)?
├─ SÍ → ¿Kill Switch activo? → NO → Es el motivo (trades zombie en rebotes)
├─ ¿SL muy amplio en algún par? → revisar ADN tabla sección 3.4
└─ REPORTAR antes de continuar, no lanzar hyperopt sobre un baseline roto

¿Error AttributeError .value?
└─ Buscar el parámetro → ¿es DecimalParameter/IntParameter? 
    ├─ SÍ → .value es correcto → otro error
    └─ NO → quitar .value, es ya un valor fijo
```

---

## 8. AUTOPSIA Y LECCIONES APRENDIDAS

### 8.1 Sesión 2026-04-05 — Crash Agosto 2024 (2h+ perdidas)

#### Problema 1: Datos inexistentes
- **Lo que pasó:** Lanzamos backtest para Agosto 2024, 0 trades, loop de comandos
- **Causa real:** Los datos de Agosto no estaban descargados en disco
- **Fix:** `list-data` SIEMPRE antes de cualquier backtest. Si no están → `download-data`
- **Tiempo perdido:** ~2 horas

#### Problema 2: Config en modo spot
- **Lo que pasó:** Los shorts no se abrían, el bot tomaba longs
- **Causa real:** Container anterior tenía cache con config de spot
- **Fix:** `docker rm -f` el container anterior antes de lanzar nuevo backtest
- **Tiempo perdido:** ~1 hora

#### Problema 3: AttributeError en Época 7 ULTRA
- **Lo que pasó:** `AttributeError: 'int' object has no attribute 'value'`
- **Causa real:** En la versión ULTRA los parámetros se convirtieron a constantes fijas pero seguían llamando `.value`
- **Fix:** Línea 128 — quitar `.value` de parámetros constantes
- **Tiempo perdido:** ~30 minutos

#### Problema 4: Agent loop
- **Lo que pasó:** El agente repitió el mismo comando fallido 3+ veces sin reportar
- **Causa real:** Sin verificación de estado real antes de ejecutar
- **Fix:** **REGLA INVIOLABLE** — Si el mismo approach falla 2 veces → PARAR → reportar al Capitán
- **Tiempo perdido:** ~1 hora

### 8.2 Fallos Críticos Descubiertos en Bear ULTRA (Agosto 2024)

| Fallo | Impacto | Fix Requerido |
|-------|---------|---------------|
| Trades Zombie (BNB 19d, BTC 15d) | Ocupan capital infinitamente | Kill Switch 1m + timeout 48h |
| 2 liquidaciones (BNB, ADA) | -92% en esas posiciones | SL más estricto por par |
| Kill Switch 1m desactivado | Rebotes violentos destruyen gains | RE-ACTIVAR URGENTE |
| Profit final solo +2.48% | 91% winrate pero perdedores se comieron todo | Gestión de pérdidas antes que ganancias |

### 8.3 Lecciones Permanentes

| Lección | Detalle |
|---------|---------|
| **Master Switch es vida o muerte** | Sin él, -40% en laterales. Con él, +118% en 5 meses |
| **Kill Switch 1m es obligatorio en Live** | Un trade zombie puede borrar semanas de profit |
| **x5 leverage exige SL estricto** | DD > 30% en futuros puede ser fatal |
| **Verificar datos ANTES** | `list-data` es el primer comando, siempre |
| **Limpiar containers antes de test** | Cache de config anterior puede sabotear el test |
| **ADN por par requiere SL calibrado** | ADA -2.2% y BNB -4.8% son insuficientes en crashs |

---

## 9. HISTORIAL DE OPTIMIZACIONES

| # | Fecha | Épocas | Timerange | Mejor Época | Profit | Notas |
|---|-------|--------|-----------|-------------|--------|-------|
| 1 | 2026-04-01 | 100 | Abr 2024 | 46 | +75.83% | ADN de Oro — Crash Agosto |
| 2 | 2026-04-01 | 100 | Jun-Jul 2024 | — | -40.01% | Zona de Muerte (sin switch) |
| 3 | 2026-04-01 | OOS | Ago 2024 | — | -1.41% | Validación inter-mercado |

### Backtests de Validación

| Escenario | Periodo | Mercado | Profit | Drawdown | Conclusión |
|-----------|---------|---------|--------|----------|------------|
| Crash Agosto | Ago 2024 | -20% | **+75.83%** | 12.21% | ADN Oro validado ✅ |
| Volatilidad Halving | Abr 2024 | -25% | +41.36% | 22.09% | Resiliencia extrema ✅ |
| Zona de Muerte | Jun/Jul 2024 | -8% | -40.01% | 47.86% | SIN SWITCH = ruina ❌ |
| Stress Test 5M | Abr-Sep 2024 | -31% | **+118.1%** | 26.04% | Switch salvó la cuenta ✅ |
| **ULTRA Agosto** | Ago 2024 | -20% | **+2.48%** | — | **Bug: sin Kill Switch 1m ⚠️** |

---

## 10. ESTADO ACTUAL (ACTUALIZAR CADA SESIÓN)

**Última actualización:** 2026-04-05

| Componente | Estado | Detalle |
|------------|--------|---------|
| Bot en AWS | ✅ Running (Dry Run) | Container activo, estrategia Bear44 |
| Estrategia activa | ✅ ChacalSniper_Bear44 | Época 46, ADN de Oro |
| Master Bear Switch | ✅ Implementado | BTC < EMA50 + ATR expandido |
| ADN por par | ✅ Optimizado | Época 46 — 8 pares |
| Kill Switch 1m ULTRA | ❌ DESACTIVADO | **PENDIENTE REACTIVAR — Bug crítico** |
| Git sincronización | ⚠️ PENDIENTE VERIFICAR | Muchos cambios locales sin push |
| Hyperopt Agosto (ULTRA) | ⚠️ Con bugs | Completado pero resultados inválidos sin Kill Switch |

### Próxima Acción Obligatoria
```
1. Verificar git status y sincronizar con AWS
2. En ChacalSniper_Bear_ULTRA.py: reactivar Kill Switch 1m
3. Ajustar SL de ADA (de -2.2% a mínimo -5%) y BNB (de -4.8% a -6%)
4. Re-correr backtest Agosto 2024 con fixes aplicados
5. Si resultado > +40% → commitear y deployar en AWS
```

---

## 11. PENDIENTES Y ROADMAP

### 🔴 INMEDIATO (bloquea producción)
- [ ] Re-activar Kill Switch 1m en Bear_ULTRA
- [ ] Ajustar SL: ADA min -5%, BNB min -6%
- [ ] Verificar y sincronizar Git local ↔ AWS
- [ ] Re-validar backtest Agosto con fixes

### 🟡 ESTA SEMANA
- [ ] Validar Bear en Oct 2024 (otro período bajista confirmado)
- [ ] Validar Bear en Ene 2025
- [ ] Optimizar Master Switch (¿más filtros de tendencia?)

### 🟢 ROADMAP
- [ ] Modo híbrido Bear + Volume (switch automático de bots)
- [ ] Agregar más pares al ADN (actualmente 8)
- [ ] Dashboard de performance en Telegram
- [ ] Transición a Live (cuando 30 días Dry Run positivos)

---

## 12. COMANDOS DE REFERENCIA RÁPIDA

```cmd
REM === SSH ===
ssh -i skills\llave-sao-paulo.pem ec2-user@15.229.158.221

REM === ESTADO BOT ===
ssh -i skills\llave-sao-paulo.pem ec2-user@15.229.158.221 "docker ps && docker logs --tail 20 Chacal_Sniper_AWS_Env"

REM === REINICIAR BOT ===
ssh -i skills\llave-sao-paulo.pem ec2-user@15.229.158.221 "cd /home/ec2-user/freqtrade && docker-compose down && docker-compose up -d"

REM === BACKTEST LOCAL (futuros) ===
docker run --rm -v "C:\CHACAL_ZERO_FRICTION\PROJECT_SNIPER_AWS\user_data:/freqtrade/user_data" freqtradeorg/freqtrade:stable backtesting --config /freqtrade/user_data/configs/config_backtest.json --strategy ChacalSniper_Bear_ULTRA --timerange 20240801-20240901 --datadir /freqtrade/user_data/data/binance/futures --data-format json --exchange binance

REM === VERIFICAR DATOS ===
docker run --rm -v "C:\CHACAL_ZERO_FRICTION\PROJECT_SNIPER_AWS\user_data:/freqtrade/user_data" freqtradeorg/freqtrade:stable list-data --config /freqtrade/user_data/configs/config_backtest.json --datadir /freqtrade/user_data/data/binance/futures

REM === MCP (si disponible) ===
REM freqtrade_control → status / profit / daily / reload_strategy / balance
```

---

> **⚡ RECORDATORIO FINAL:** Este es el cerebro del Sniper Bear.
> Cualquier agente que retome el trabajo DEBE leer este archivo primero.
> Leer también `PEGASO_MASTER_PROMPT.md` para contexto del ecosistema completo.
> Actualizar **Sección 10 (Estado Actual)** después de cada acción significativa.