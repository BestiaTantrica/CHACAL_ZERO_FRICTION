# 📊 CHACAL MASTER ESTADO — TABLERO GLOBAL (V5.1 FAN-HUNTER)

> **Última actualización:** 2026-04-20
> **Ecosistema:** FONDO DE INVERSIÓN TRIFÁSICO + FAN-HUNTER EXPANSION 🦅🦊🐺
> **Estado:** 🟡 PARCIALMENTE OPERATIVO (AWS sin trades — Auditoría pendiente mañana)
> **Hilo de Monitoreo Directo:** [MONITOREO_TRIFASICO.md](file:///c:/CHACAL_ZERO_FRICTION/MONITOREO_TRIFASICO.md)

---

## 🏗️ ARQUITECTURA ACTUAL

1. 🦅 **SNIPER BEAR (7x) - AWS:** Modo Bear. **⚠️ SIN TRADES — AUDITAR URGENTE mañana 21/04.**
2. 🦊 **VOLUME HUNTER (10x) - AWS:** Modo Bull. Standby según EMA50 BTC.
3. 🐺 **CHACAL LATERAL V5 (5x) - ORACLE:** Mercado Lateral. Pares: BTC, SOL, LINK, AVAX. (IP: 129.80.104.116 via Brasil Proxy).
4. 🎯 **FAN-HUNTER (nuevo) - ORACLE:** Estrategia especialista en tokens de espectáculo. En diseño. Ver sección abajo.

---

## 🎯 PROYECTO FAN-HUNTER — ESTADO DEL LABORATORIO (20/04/2026)

### Cuarteto Validado (Provisionalmente)

| Token | Perfil | Mejor Día | Net 6M (ese día) | WinRate | Veredicto |
|---|---|---|---|---|---|
| **OG** | Solo Short | Domingo | +19.4% | 70% | ✅ CONFIRMADO |
| **BAR** | Dual | Viernes | +53.5% | 78% | ✅ CONFIRMADO — Opera TODA la semana |
| **WIF** | Solo Short | Dom/Sab | +127% | 82% | ✅ ESTRELLA — Opera TODA la semana |
| **APE** | Solo Dom | Domingo | +15.2% | 61% | ⚠️ CANDIDATO DÉBIL — Solo domingo funciona |

### Hallazgo Clave: EL SESGO DE FIN DE SEMANA ERA FALSO

Análisis de 180 días (6 meses) de datos 1m confirmó:
- **BAR** genera el 74% de su rentabilidad de LUNES a VIERNES.
- **WIF** opera con profit todos los 7 días (min: +49% el martes, max: +127% el domingo).
- **OG** sí tiene sesgo finde (Dom+Jue=33 puntos, el resto pierde).
- **APE** PIERDE en 6 de 7 días. Solo el domingo es positivo.

### ⚠️ APE Necesita Reemplazo

APE no cumple el criterio mínimo de **rentabilidad en al menos 4 días/semana**. 

**Próximo paso de mañana:** Scannear candidatos alternativos a APE con el script
`research_dayofweek_cycles.py` modificado para candidatos:
- **FLOKI** — Ya testeado finde (+5.06%, WR 78.9%). Opera en modo Dual.
- **BONK** — WR 91.3% en finde (sospechoso, confirmar histórico).
- **NOT** — +4.35% finde, ecosistema Telegram (miles de eventos diarios).
- **DOGE** — Comunidad masiva, revisar patrón semanal.

**Criterio de admisión:** Net positivo en mínimo 4 de 7 días con WR > 65%.

---

## 📋 HOJA DE RUTA — PRÓXIMOS PASOS (ORDENADOS POR PRIORIDAD)

### 🔴 URGENTE — Mañana 21/04

1. **AUDITAR AWS (Sniper Bear + Volume Hunter)**
   - Sin trades desde hace días. Verificar si el orquestador está corriendo.
   - Comandos AWS: `systemctl status chacal-control` / `journalctl -u ft-bear -n 100`
   - Si no hay trades en modo Dry Run: revisar threshold EMA50 y señales de entrada.

2. **Completar Cuarteto Fan-Hunter (reemplazar APE)**
   - Correr `research_dayofweek_cycles.py` con FLOKI, BONK, NOT, DOGE.
   - Elegir el que tenga profit en 4+ días con WR > 65%.

### 🟡 ESTA SEMANA

3. **Preparar estrategia Fan-Hunter para Dry Run en Oracle**
   - Crear `strategies/ChacalFanHunter_V1.py` basada en V4 (Z-Score + RSI).
   - Configurar instancia Oracle con los 3 tokens confirmados (OG, BAR, WIF).
   - Dry Run inicial con stake simulado.

4. **Calendario de Eventos por Token**
   - OG: Calendario Dota2/CS torneos (ESL, BLAST) → activo Jue-Dom.
   - BAR: Calendario La Liga + Champions League → activo toda la semana, pico Vie.
   - WIF: Sin calendario fijo, opera continuo. Boost en bull runs de Solana.
   - Token #4 (por confirmar): según su ecosistema.

### 🟢 PRÓXIMA SEMANA

5. **Pasar Fan-Hunter de Dry Run a Live con stake mínimo** (10 USDT/trade).
6. **Sistema de calendario inteligente**: El bot consulta próximos eventos del token
   para escalar el stake (normal → x1.5 si hay evento conocido ese día).

---

## 🗺️ MAPA DE ARCHIVOS — FAN-HUNTER

| Archivo | Descripción | Estado |
|---|---|---|
| `scripts/research_weekend_test.py` | Test rápido fin de semana para candidatos | ✅ Listo |
| `scripts/research_dayofweek_cycles.py` | Análisis histórico 7 días × 6 meses | ✅ Listo |
| `scripts/research_historical_cycles.py` | Test multi-semana (versión antigua) | ⚠️ Unicode fix pendiente |
| `research_data/dayofweek_analysis.csv` | Resultados del análisis de 6 meses | ✅ Generado |
| `research_data/weekend_summary_utf8.txt` | Resultados finde 17-19 Abr | ✅ Generado |
| `strategies/ChacalFanHunter_V1.py` | Estrategia para Freqtrade | ⏳ PENDIENTE |

---

## 🚦 KPIs DE LABORATORIO (ACTUALIZADO)

| Estrategia | ROI Validado | Timeframe | Estado |
|---|---|---|---|
| **Lateral V5** (Oracle) | +45-52%/año | Continuo | 🟢 Operativo |
| **Sniper Bear** (AWS) | +527% histórico | Bear market | 🔴 Sin trades |
| **Volume Hunter** (AWS) | Standby | Bull market | 🟡 Esperando |
| **Fan-Hunter WIF** | +625% en 6m (backtest) | Lun-Dom | 🔬 En laboratorio |
| **Fan-Hunter BAR** | +202% en 6m (backtest) | Lun-Dom | 🔬 En laboratorio |
| **Fan-Hunter OG** | +56% en 6m (backtest) | Jue-Dom | 🔬 En laboratorio |

---

## ⚠️ ALERTAS ACTIVAS

- **AWS Sniper Bear: SIN ACTIVIDAD** — Prioridad 1 para auditoría mañana.
- **APE descartado** del cuarteto Fan-Hunter por pérdidas en 6/7 días.
- **Dry Run Fan-Hunter aún no iniciado** — pendiente definir token #4.

---

*El camino a la rentabilidad real: AWS activo + Fan-Hunter en Dry Run = dos frentes simultáneos.*
