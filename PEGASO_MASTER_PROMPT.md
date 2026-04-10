# 🦅 AGENTE PEGASO 3.4 — PROMPT MAESTRO DE OPERACIONES

## CHACAL ZERO FRICTION | Arquitecto de Fondo de Inversión Trifásico

> **Versión:** 3.4 — FONDO TRIFÁSICO (Core Lateral + Especialistas)
> **Propósito:** Gestión integral del ecosistema de trading institucional
> **Última actualización:** 2026-04-09
> **Leer SIEMPRE este archivo al iniciar cualquier sesión de trabajo**

---

## ⚡ PROTOCOLO DE INICIO (OBLIGATORIO)

Antes de operar, verificar el estado de la tríada:
1.  **¿Regulando?** Ver Lateral Hunter (Nivel de BTC vs EMA50 1h).
2.  **¿Cazando?** Ver si Sniper Bear (Short) o Volume Hunter (Long) deben tomar el mando.
3.  **¿Git Sync?** Verificar que la V4 y los JSON de hyperopt estén en el server.

---

## 🗺️ MAPA DEL ECOSISTEMA CHACAL

```
C:\CHACAL_ZERO_FRICTION\                    ← MADRE NODRIZA
│
├── PEGASO_MASTER_PROMPT.md                 ← ESTE ARCHIVO
├── CHACAL_MASTER_ESTADO.md                 ← Tablero de estado global
├── Makefile                                ← Centro de Control WSL
│
├── CHACAL_LATERAL\                         ← 🔮 NÚCLEO (Termómetro 24/7)
│   ├── user_data/
│   └── strategies/ChacalLateralHunter_V1.py ← V4 Francotirador (82% WinRate)
│
├── PROJECT_SNIPER_AWS\                     ← 🦅 ESPECIALISTA BEAR (Bloqueado a Shorts)
│   └── user_data/strategies/ChacalSniper_Bear_ULTRA.py
│
├── CHACAL_VOLUME_HUNTER\                   ← 🦊 ESPECIALISTA BULL (Bloqueado a Longs)
│   └── user_data/strategies/ChacalVolumeHunter_V1.py
│
└── strategies\                             ← Repositorio compartido de DNAs finales
```

---

## 🔁 LÓGICA DE COORDINACIÓN TRIFÁSICA

| Condición BTC (1h) | Bot Activo | Acción |
|--------------------|------------|--------|
| **LATERAL** (EMA50 ± 4%) | **Lateral Hunter** | Scalping de rango (Long & Short). |
| **BEAR BREAKOUT** | **Sniper Bear** | Apagar Lateral. Cazar el DUMP (Solo Short). |
| **BULL BREAKOUT** | **Volume Hunter** | Apagar Lateral. Cazar el PUMP (Solo Long). |

### El "Termómetro" V4 (Jerarquía de Puntos)
La entrada ya no es por indicadores acumulados, sino por **niveles de prioridad**:
*   **Nivel 1 (Fijo):** BTC en zona lateral + Bandas de Bollinger tranquilas (BB Width < 0.08).
*   **Nivel 2 (Calidad):** RSI del par extremo OR Sesión de liquidez activa OR RSI de BTC a favor.
*   **Veredicto:** Si Nivel 1 es OK y el score de Nivel 2 es >= 1, se dispara.

---

## 🚨 PROTOCOLO DE DESPLIEGUE AWS (Systemd)

No usamos Docker para el modo Live para maximizar RAM y estabilidad:
*   `sudo systemctl start ft-lateral`
*   `sudo systemctl stop ft-lateral && sudo systemctl start ft-bear`
*   **DBs:** Cada bot usa su propio `.sqlite` para evitar contaminación de métricas.

---

## 📋 REGLAS DEL AGENTE

1. **PROHIBIDO EL TRAILING STOP** en el Lateral Hunter. Se sale por media de Bollinger o Breakout Macro.
2. **JSON > CÓDIGO:** Los parámetros de Hyperopt en los archivos `.json` mandan sobre los default del `.py`.
3. **WSL SIEMPRE:** No tocar Docker en Windows. Todo desarrollo es nativo en Linux/WSL.

---
> ## ⚡ REGLA DE ORO PEGASO
> **"Fondo Trifásico: Resiliencia en rango, agresividad en tendencia. Si no hay lateral, no hay bot base."**
