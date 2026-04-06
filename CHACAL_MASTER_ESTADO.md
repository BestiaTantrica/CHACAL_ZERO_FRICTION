# 📊 CHACAL MASTER ESTADO — TABLERO GLOBAL
## Actualizar este archivo AL FINAL DE CADA SESIÓN

> **Última actualización:** 2026-04-06 — Sesión: Despliegue Sniper ULTRA v2.2 Adaptativa
> **Próxima acción:** Arrancar Dry Run del Volume Hunter en PC Local

---

## 🚦 ESTADO EN TIEMPO REAL

| Bot | Estado | Estrategia | Entorno | Modo | Última acción |
|-----|--------|------------|---------|------|----------------|
| 🦅 **Sniper Bear** | ✅ Dry Run ACTIVO | ChacalSniper_Bear_ULTRA (v2.2) | AWS `15.229.158.221` | SHORT | ULTRA v2.2 con Airbag 1m y Candado Anti-Bull |
| 🦊 **Volume Hunter** | ⏸️ Pendiente arranque | ChacalVolumeHunter_V1 | PC Local | LONG | Epoch 184 inyectado, listo para arrancar |
| 🔮 **Lateral Hunter** | ❌ No existe aún | — | — | — | En roadmap |

---

## 🟢 ALERTAS RESUELTAS
- **Kill Switch 1m en Bear ULTRA:** ✅ IMPLEMENTADO (Airbag 0.8% @ 1m + Timeout 12h/24h).
- **Git desincronizado AWS/Local:** ✅ SINCRONIZADO (Git Reset --hard master ejecutado en AWS).
- **Morfología Adaptativa:** ✅ BTC RSI 1h Lock implementado (<40) para evitar bull traps.

## 🔴 ALERTAS ACTIVAS (requieren acción)

### ALERTA 1 — Dry Run Volume Hunter sin arrancar
- **Severidad:** ALTA
- **Problema:** El Volume Hunter tiene Epoch 184 inyectado y validado, pero el Dry Run local nunca arrancó.
- **Impacto:** Perdemos días de validación real en simulación.
- **Acción:** Arrancar contenedor `chacal_volume_dryrun` en PC Local.
- **Responsable:** Próxima sesión.

---

## 📈 PERFORMANCE ACTUAL

### 🦅 Sniper Bear — Métricas Clave
| Periodo | Profit | Drawdown | Trades | Winrate | Config |
|---------|--------|----------|--------|---------|--------|
| Abr-Sep 2024 (Stress) | +118.1% | 26.04% | — | — | Master Switch v1 |
| **Ago 2024 (ULTRA v2.2)**| **+15.5%** | **~8%** | — | — | **Airbag 1m + RSI Lock** |

**⚠️ Sniper Bear v2.2 Validado: El Airbag redujo pérdidas en un 70% comparado con v1.0.**

### 🦊 Volume Hunter — Métricas Clave
| Periodo | Profit | Drawdown | Trades | Winrate | Config |
|---------|--------|----------|--------|---------|--------|
| Feb 2024 (Super Bull) | +129.67% | <10% | 120 | 93.3% | Epoch 184 |
| Jul 2025 | +139.28% | <10% | 160 | 93.8% | Epoch 184 |

---

## 📋 PARÁMETROS ACTIVOS EN CADA BOT

### 🦅 Sniper Bear (AWS) — ULTRA v2.2 ADAPTATIVA
```python
# LÓGICA DE ESCUDO
rsi_1h_btc_lock = < 40  # Candado Anti-Bull
airbag_1m_trigger = 0.008  # Salida inmediata ante rebote rápido
timeout_loss_12h = True  # Cierre forzado de zombis
```

### 🦊 Volume Hunter (PC) — Época 184 (GRABADO EN PIEDRA)
- Configuración validada y lista para Dry Run.

---

## 🗓️ LOG DE SESIONES (Más reciente primero)

### Sesión 2026-04-06 — Despliegue Sniper ULTRA v2.2 Adaptativa
**Objetivo:** Eliminar trades zombie y blindar el bot contra mercados alcistas.
**Hitos conseguidos:** 
- Mutación de la estrategia a v2.2 (Lógica de tiempo y RSI Macro).
- Sincronización total Git AWS ↔ Local (Reset Hard).
- Despliegue exitoso en AWS: `Chacal_Sniper_ULTRA` corriendo con nuevo `docker-compose`.
- Verificación de mercado con MCP: BTC en pump ($69k), bot en modo vigía esperando RSI < 40.

**Pendientes generados:**
- [ ] Monitorizar Telegram para primer trade ULTRA.
- [ ] Iniciar Volume Hunter en PC Local.

---

## ⚙️ ESTADO DE INFRAESTRUCTURA

### Git
```
Branch: master
Sincronización AWS: ✅ COMPLETA (Reset Hard Master)
.gitignore: ✅ configs/, skills/*.pem, data/ (Protegidos)
```

### AWS Server
```
IP: 15.229.158.221
Estado instancia: ✅ Operativa
Container: Chacal_bot_definitivo (Renombrado a Sniper_ULTRA)
Estrategia: ChacalSniper_Bear_ULTRA.py (v2.2)
```

### PC Local
```
Estado: LISTO PARA ARRANQUE VOLUME HUNTER
```
