# 📊 CHACAL MASTER ESTADO — TABLERO GLOBAL
## Actualizar este archivo AL FINAL DE CADA SESIÓN

> **Última actualización:** 2026-04-05 — Sesión: Autopsia Crash Agosto + ULTRA bugs
> **Próxima acción:** Re-activar Kill Switch 1m en Bear ULTRA y validar con datos limpios

---

## 🚦 ESTADO EN TIEMPO REAL

| Bot | Estado | Estrategia | Entorno | Modo | Última acción |
|-----|--------|------------|---------|------|----------------|
| 🦅 **Sniper Bear** | ✅ Dry Run ACTIVO | ChacalSniper_Bear_ULTRA | AWS `15.229.158.221` | SHORT | Autopsia Agosto - bugs identificados |
| 🦊 **Volume Hunter** | ⏸️ Pendiente arranque | ChacalVolumeHunter_V1 | PC Local | LONG | Epoch 184 inyectado, Dry Run pendiente |
| 🔮 **Lateral Hunter** | ❌ No existe aún | — | — | — | En roadmap |

---

## 🔴 ALERTAS ACTIVAS (requieren acción)

### ALERTA 1 — Kill Switch 1m en Bear ULTRA
- **Severidad:** CRÍTICA
- **Problema:** El Kill Switch de 1m está desactivado en la versión ULTRA. El backtest de Agosto 2024 mostró trades zombie (BNB 19 días, BTC 15 días) y 2 liquidaciones.
- **Impacto:** En Live, estas posiciones destruirían la cuenta.
- **Acción:** Reactivar `rsi_kill_switch` en timeframe 1m + timeout de 48h máximo
- **Responsable:** Próxima sesión con código

### ALERTA 2 — Git desincronizado (PENDIENTE VERIFICAR)
- **Severidad:** ALTA
- **Problema:** Se hicieron muchos cambios locales sin commitear ni pushear al server
- **Impacto:** AWS podría estar corriendo estrategia desactualizada
- **Acción:** 
  ```cmd
  git status
  git log --oneline -10
  ssh -i skills\llave-sao-paulo.pem ec2-user@15.229.158.221 "cd /home/ec2-user/freqtrade && git log --oneline -5"
  ```
- **Responsable:** INMEDIATO al inicio de próxima sesión

### ALERTA 3 — Dry Run Volume Hunter sin arrancar
- **Severidad:** MEDIA
- **Problema:** El Volume Hunter tiene Epoch 184 inyectado y validado, pero el Dry Run local nunca arrancó.
- **Impacto:** Perdemos días de validación real en simulación
- **Acción:** Ver sección 16 de INSTRUCCIONES_CLINE_VOLUME.md
- **Responsable:** Próxima sesión de Volume

---

## 📈 PERFORMANCE ACTUAL

### 🦅 Sniper Bear — Métricas Clave
| Periodo | Profit | Drawdown | Trades | Winrate | Config |
|---------|--------|----------|--------|---------|--------|
| Abr 2024 (Hyperopt) | +75.83% | 12.21% | 175 | 90.9% | Época 46 (ADN Oro) |
| Abr-Sep 2024 (5M) | +118.1% | 26.04% | — | — | Con Master Switch |
| **Ago 2024 (ULTRA)** | **+2.48%** | **—** | 175 | 91.4% | **Bug: sin Kill Switch** |

**⚠️ Epóca 7 ULTRA tiene bug crítico — NO usar en live hasta fix**

### 🦊 Volume Hunter — Métricas Clave
| Periodo | Profit | Drawdown | Trades | Winrate | Config |
|---------|--------|----------|--------|---------|--------|
| Feb 2024 | +129.67% | <10% | 120 | 93.3% | Epoch 184 |
| Jul 2025 | +139.28% | <10% | 160 | 93.8% | Epoch 184 |
| May 2024 | +73.41% | <8% | 84 | 90.5% | Epoch 184 |
| Ene 2024 | +0.06% | <5% | 56 | 82.1% | Epoch 184 (protección) |
| Sep 2024 | +62.20% | 8.17% | 70 | 88.6% | Epoch 184 |

---

## 📋 PARÁMETROS ACTIVOS EN CADA BOT

### 🦅 Sniper Bear (AWS) — Época 46 (ADN DE ORO - STABLE)
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
> ⚠️ La versión ULTRA (Época 7) tiene bugs. Usar esta configuración en producción.

### 🦊 Volume Hunter (PC) — Época 184 (GRABADO EN PIEDRA)
```python
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
trailing_stop_positive = 0.302
trailing_stop_positive_offset = 0.391
```

---

## 🗓️ LOG DE SESIONES (Más reciente primero)

### Sesión 2026-04-05 — Autopsia Crash Agosto 2024
**Objetivo:** Validar ChacalSniper_Bear_ULTRA contra Agosto 2024
**Lo que pasamos:** 
- ~2h buscando datos que no existían → **Lección: verificar datos PRIMERO**
- ~1h con config en modo spot → **Lección: limpiar container antes de test**  
- ~30m con AttributeError .value en Época 7 → **Fix: línea 128 estrategia**
- ~1h de agent loop repitiendo comandos → **Lección: si falla 2 veces, PARAR**

**Resultados Bear ULTRA (Agosto 2024):**
- Profit: +2.48% (vs +75.83% esperado con ADN de Oro)
- Problema: 2 liquidaciones en BNB/ADA, trades zombie de 15-19 días
- Sin Kill Switch 1m = ruina garantizada en producción

**Pendientes generados:**
- [ ] Re-activar Kill Switch 1m
- [ ] Revisar SL por par (BNB, ADA)
- [ ] Commitear TODO el trabajo de hoy

---

### Sesión 2026-04-04 — Volume Hunter Multi-Mercado
**Objetivo:** Validar Volume Hunter en diferentes regímenes de mercado
**Resultado:** ✅ 5 periodos validados, DD siempre <10%, filtro BTC EMA50 funciona
**Pendiente:** Arrancar Dry Run local

---

### Sesión 2026-04-03 — Hyperopt Volume Super Bull
**Objetivo:** Optimizar Volume Hunter para Super Bull (Feb 2024)
**Resultado:** ✅ Época 184 = +129.67% en Feb 2024
**Pendiente:** Deploy Dry Run

---

### Sesión 2026-04-02 — Volume Hunter Baseline
**Objetivo:** Establecer baseline estable Volume Hunter
**Resultado:** ✅ +5.59% Julio 2025 (28 pares), +9.67% (8 pares)
**Pendiente:** Hyperopt escenario lateral

---

### Sesión 2026-04-01 — Bear Strategy & AWS
**Objetivo:** Optimizar Sniper Bear y conectar AWS
**Resultado:** ✅ Época 46 ADN Oro +75.83%, Master Switch implementado, Git conectado
**Pendiente:** Más periodos de validación

---

## ⚙️ ESTADO DE INFRAESTRUCTURA

### Git
```
Branch: master
Último commit conocido: [PENDIENTE VERIFICAR]
Sincronización AWS: ⚠️ PENDIENTE VERIFICAR
.gitignore: ✅ configs/, skills/*.pem, data/ excluidos
```

### AWS Server
```
IP: 15.229.158.221
Estado instancia: ✅ Running
Container Bear: ✅ Chacal_Sniper_AWS_Env (Dry Run)
Estrategia en server: ⚠️ PENDIENTE VERIFICAR (git pull requerido)
```

### PC Local
```
CPU: i3-4170 | RAM: 10GB
Container Volume: ⏸️ chacal_volume_dryrun (pendiente arrancar)
Docker limits: --memory 7g --cpus 2
```

---

## 📌 PLANTILLA PARA PRÓXIMA SESIÓN

```
## Sesión YYYY-MM-DD — [Título]
**Objetivo:** 
**Proyecto:** [Bear/Volume/Lateral]
**Duración:** 

**Acciones ejecutadas:**
1. 
2. 

**Resultados:**
- Profit: 
- Drawdown: 
- Trades: 

**Problemas encontrados:**
- 

**Pendientes generados:**
- [ ] 

**Próxima sesión debería:**
1. 
```
