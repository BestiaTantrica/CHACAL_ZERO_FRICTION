# 🦅 CHACAL SNIPER BEAR - MAESTRO DE OPERACIONES

> **Última actualización:** 2026-04-02
> **Versión:** 1.0
> **Proyecto:** PROJECT_SNIPER_AWS (Servidor AWS)
> **Compañero:** CHACAL_VOLUME_HUNTER (PC Local - Bull/Long)

---

## 1. IDENTIDAD Y MISIÓN

**CHACAL SNIPER BEAR** es la estrategia hermana del Volume Hunter. Mientras el Volume Hunter caza en subidas (Bull/Long), el Sniper caza en caídas (Bear/Short).

| Aspecto | Sniper Bear (este) | Volume Hunter (PC) |
|---------|-------------------|-------------------|
| Entorno | AWS `15.229.158.221` | PC Local |
| Modo | Solo SHORT | Solo LONG |
| Mercado | BEAR | BULL / LATERAL |
| Motor | Pivotes + ADN por par | Volumen + Correlación BTC |
| Horario | 24/7 | 06-20 UTC |
| Apalancamiento | x5 | x3 (implícito) |

**Filosofía:** El Sniper espera que BTC rompa la EMA 50 (1h) con volatilidad expandida (ATR > promedio). Cuando el Master Bear Switch se activa, caza shorts usando ADN optimizado por par. Cada par tiene su propio "código genético" de parámetros.

---

## 2. ARQUITECTURA TÉCNICA

### 2.1 Servidor AWS
| Parámetro | Valor |
|-----------|-------|
| IP | `15.229.158.221` |
| Usuario | `ec2-user` |
| Llave SSH | `skills/llave-sao-paulo.pem` |
| Path Freqtrade | `/home/ec2-user/freqtrade` |
| Región | São Paulo |

### 2.2 Estructura de Archivos
```
PROJECT_SNIPER_AWS/
├── INSTRUCCIONES_CLINE_BEAR.md  ← ESTE ARCHIVO (maestro)
├── docker-compose.yml           ← Servicio Docker en AWS
└── user_data/
    ├── strategies/
    │   └── ChacalSniper_Bear44.py  ← Estrategia principal
    └── configs/                   ← NO subir a Git (tokens)
```

### 2.3 Reglas de Seguridad
- ❌ **NUNCA subir** `user_data/configs/` a Git (tokens Telegram, claves Binance)
- ❌ **NUNCA subir** `skills/llave-sao-paulo.pem` a Git
- ✅ `.gitignore` bloquea estas carpetas
- ✅ Secrets solo viven en el servidor y tu PC

---

## 3. ESTRATEGIA: ChacalSniper_Bear44

### 3.1 Lógica de Entrada (SNIPER_BEAR_SHORT)

```
Condiciones TODAS deben cumplirse:
1. master_bear_switch == 1 (BTC < EMA50 1h AND ATR > promedio 24h)
2. Volumen > media 20 velas × volume_mult
3. Cambio precio < -0.1% (price_change negativo)
4. RSI < rsi_bear_thresh
5. RSI cayendo (rsi < rsi.shift(1))
6. Precio < Bollinger mid band
7. ADX > adx_threshold (tendencia fuerte)
```

### 3.2 Lógica de Salida

| Salida | Condición |
|--------|-----------|
| `bear_roi_hit` | Profit ≥ roi_target (DNA del par × roi_base × 0.8) |
| `rsi_kill_switch_short` | RSI > rsi_kill_switch AND ADX > adx_threshold |
| `trailing_stop` | Se activa a +2.5%, persigue dejando 1% de aire |
| `custom_stoploss` | DNA del par (bear_sl) o default -7.5% |

### 3.3 Master Bear Switch
```
btc_trend_bear = BTC_close < BTC_EMA50(1h)
btc_vol_active = BTC_ATR > BTC_ATR_mean(24h)
master_bear_switch = btc_trend_bear AND btc_vol_active
```
Cuando el switch está OFF (mercado lateral/alcista), NO abre shorts. Es la protección principal.

### 3.4 ADN por Par (Código Genético)

| Par | v_factor | pulse_change | bear_roi | bear_sl |
|-----|----------|-------------|----------|---------|
| BTC | 4.660 | 0.004 | 2.2% | -3.1% |
| ETH | 5.769 | 0.004 | 1.8% | -3.1% |
| SOL | 5.386 | 0.001 | 4.2% | -4.0% |
| BNB | 3.378 | 0.003 | 1.1% | -4.8% |
| XRP | 5.133 | 0.004 | 4.2% | -5.4% |
| ADA | 3.408 | 0.005 | 4.2% | -2.2% |
| AVAX | 5.692 | 0.005 | 1.0% | -5.3% |
| LINK | 5.671 | 0.005 | 3.8% | -4.1% |

### 3.5 Parámetros Hyperoptables

| Parámetro | Espacio | Rango | Default | Descripción |
|-----------|---------|-------|---------|-------------|
| `v_factor_mult` | buy | 0.3-2.0 | 1.323 | Multiplicador del factor de volumen |
| `adx_threshold` | buy | 15-35 | 26 | ADX mínimo para confirmar tendencia |
| `rsi_bear_thresh` | buy | 20-50 | 30 | RSI máximo para entrar short |
| `volume_mult` | buy | 0.5-2.5 | 1.44 | Multiplicador de volumen mínimo |
| `roi_base` | sell | 1%-8% | 4.5% | ROI base para salida |
| `rsi_kill_switch` | sell | 35-60 | 48 | RSI para kill switch |
| `bear_stoploss` | sell | -25% a -1% | -9.0% | Stoploss por par |

### 3.6 Pares Operables (8)
```
BTC/USDT:USDT    ETH/USDT:USDT    SOL/USDT:USDT    BNB/USDT:USDT
XRP/USDT:USDT    ADA/USDT:USDT    AVAX/USDT:USDT   LINK/USDT:USDT
```

---

## 4. CONFIGURACIÓN AWS

### 4.1 Config de Trading
| Parámetro | Valor |
|-----------|-------|
| Trading Mode | Futures |
| Margin Mode | Isolated |
| Leverage | x5 (fijo en estrategia) |
| Max Open Trades | 8 |
| Stake | Unlimited (balance ratio) |
| Tradable Balance Ratio | 0.90 |
| Timeframe | 5m |

### 4.2 Docker Compose
```yaml
services:
  freqtrade:
    image: freqtradeorg/freqtrade:stable
    container_name: Chacal_Sniper_AWS_Env
    shm_size: '2gb'
    volumes:
      - "./user_data:/freqtrade/user_data"
    environment:
      - FREQTRADE_WORKERS=1
      - PAGER=cat
    entrypoint: /bin/bash
    command: ["-c", "trap : TERM INT; tail -f /dev/null & wait"]
```

---

## 5. HISTORIAL DE OPTIMIZACIONES

| # | Fecha | Épocas | Timerange | Mejor Época | Profit | Notas |
|---|-------|--------|-----------|-------------|--------|-------|
| 1 | 2026-04-01 | 100 | Abr 2024 | 46 | +75.83% | ADN de Oro - Crash Agosto |
| 2 | 2026-04-01 | 100 | Jun-Jul 2024 | - | -40.01% | Zona de Muerte (sin switch) |
| 3 | 2026-04-01 | OOS | Ago 2024 | - | -1.41% | Validación inter-mercado |

### Backtest Stress Test (5 meses Abr-Sep 2024)
| Configuración | Profit | Drawdown | Conclusión |
|---------------|--------|----------|------------|
| Sin Master Switch | -40.01% | 47.86% | Suicidio en laterales |
| **CON Master Switch** | **+118.1%** | **26.04%** | **HITO ALPHA** |

### Log de Validaciones Críticas

| Escenario | Periodo | Mercado | Profit | Drawdown | Conclusión |
|-----------|---------|---------|--------|----------|------------|
| Crash Agosto | Ago 2024 | -20% | **+75.83%** | 12.21% | DNA de Oro validado |
| Volatilidad Halving | Abr 2024 | -25% | +41.36% | 22.09% | Resiliencia extrema |
| Zona de Muerte | Jun/Jul 2024 | -8% | -40.01% | 47.86% | Debilidad en laterales |
| **Stress Test 5M** | Abr-Sep 2024 | -31% | **+118.1%** | 26.04% | **El Switch salvó la cuenta** |

---

## 6. ESTADO ACTUAL

**Actualizado:** 2026-04-02

| Componente | Estado |
|------------|--------|
| Bot en AWS | ✅ Running (Dry Run) |
| Estrategia | ✅ ChacalSniper_Bear44 |
| Master Switch | ✅ Activo |
| ADN por par | ✅ Optimizado (época 46) |
| Hyperopt Bear Agosto | 🔄 Completado (68/100 épocas) |

### Parámetros Actuales (Época 46 - ADN de Oro)
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

---

## 7. HITOS Y LOG

| Fecha | Evento | Decisión |
|-------|--------|----------|
| 2026-04-01 | ADN de Oro descubierto (época 46) | +75.83% en crash Agosto |
| 2026-04-01 | Master Bear Switch implementado | Salvó cuenta en Jun 2024 |
| 2026-04-01 | Validación OOS Agosto 2024 | Breakeven estratégico (-1.41%) |
| 2026-04-01 | Git conectado al server AWS | Deploy automatizado posible |

### Lecciones Aprendidas
1. **Master Switch es CRÍTICO** - Sin él, el bot se suicida en laterales (-40%)
2. **ADN por par funciona** - Cada par tiene volatilidad diferente
3. **x5 leverage exige stoploss estricto** - Drawdown >30% es peligroso
4. **Breakeven en OOS es bueno** - El DNA de Abr resiste shock de Agosto

---

## 8. WORKFLOWS ESTÁNDAR

### 8.1 Actualizar Estrategia en AWS
```bash
# 1. Hacer cambios en PC
git add PROJECT_SNIPER_AWS/ strategies/ChacalSniper_Bear44.*
git commit -m "Sniper: descripción del cambio"
git push origin master

# 2. Deploy al server
ssh -i skills\llave-sao-paulo.pem ec2-user@15.229.158.221 \
  "cd /home/ec2-user/freqtrade && git pull origin master && docker-compose down && docker-compose up -d"
```

### 8.2 Monitoreo AWS
```bash
# Ver estado del bot
ssh -i skills\llave-sao-paulo.pem ec2-user@15.229.158.221 \
  "cd /home/ec2-user/freqtrade && docker exec Chacal_Sniper_AWS_Env freqtrade status"

# Ver balance
ssh -i skills\llave-sao-paulo.pem ec2-user@15.229.158.221 \
  "cd /home/ec2-user/freqtrade && docker exec Chacal_Sniper_AWS_Env freqtrade balance"

# Ver logs recientes
ssh -i skills\llave-sao-paulo.pem ec2-user@15.229.158.221 \
  "cd /home/ec2-user/freqtrade && docker logs --tail 50 Chacal_Sniper_AWS_Env"
```

### 8.3 Reiniciar Bot
```bash
ssh -i skills\llave-sao-paulo.pem ec2-user@15.229.158.221 \
  "cd /home/ec2-user/freqtrade && docker-compose down && docker-compose up -d"
```

### 8.4 Hyperopt (en PC, datos locales)
```bash
docker run --rm -v "C:\CHACAL_ZERO_FRICTION\PROJECT_SNIPER_AWS\user_data:/freqtrade/user_data" \
  -v "C:\CHACAL_ZERO_FRICTION\strategies:/freqtrade/user_data/strategies" \
  freqtradeorg/freqtrade:stable hyperopt \
  --config /freqtrade/user_data/configs/config_backtest.json \
  --strategy ChacalSniper_Bear44 \
  --hyperopt-loss SharpeHyperOptLoss \
  --timerange 20240801-20240901 \
  --spaces buy sell \
  -e 100 -j 1 2>&1
```

### 8.5 Subir Config al Server (sin Git)
```bash
scp -i skills\llave-sao-paulo.pem \
  PROJECT_SNIPER_AWS\user_data\configs\config_aws.json \
  ec2-user@15.229.158.221:/home/ec2-user/freqtrade/user_data/configs/
```

---

## 9. PENDIENTES Y ROADMAP

### Inmediato
- [ ] Completar hyperopt Bear Agosto (68/100 épocas)
- [ ] Evaluar nuevos parámetros si mejoran el DNA de Oro
- [ ] Monitorear performance en Dry Run actual

### Mediano plazo
- [ ] Agregar más pares al ADN (actualmente 8)
- [ ] Validar en otros meses bear (Oct 2024, Ene 2025)
- [ ] Optimizar Master Switch (más filtros de tendencia)
- [ ] Transición a Live (cuando confianza sea alta)

### Largo plazo
- [ ] Modo híbrido con Volume Hunter (switch automático)
- [ ] Alertas Telegram mejoradas
- [ ] Dashboard de performance
- [ ] Backtesting continuo con nuevos datos

---

## 10. COMANDOS RÁPIDOS

### SSH al Server
```bash
ssh -i skills\llave-sao-paulo.pem ec2-user@15.229.158.221
```

### Docker en AWS
```bash
# Ver contenedores
docker ps

# Ver logs
docker logs -f Chacal_Sniper_AWS_Env

# Reiniciar
docker-compose down && docker-compose up -d
```

### MCP Freqtrade Control
```
Usar herramienta MCP: freqtrade_control
Acciones disponibles: status, profit, daily, reload_strategy, balance
```

---

> **RECORDATORIO:** Este archivo es el cerebro del proyecto Sniper Bear. Cualquier agente que retome el trabajo DEBE leer este archivo primero. Actualizar la sección 6 (Estado Actual) después de cada acción significativa.