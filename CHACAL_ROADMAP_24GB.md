# 🚀 PLAN OPERATIVO: OCI 24GB & MEDIDOR ASIMÉTRICO DE SUSTOS

> **Estado:** En espera (Deploy programado al recibir la instancia de 24GB).
> **Objetivo:** Operación paralela al Fondo Trifásico, enfocada 100% en el comportamiento individual de las altcoins (desacoplado de BTC).

---

## 1. LA VISIÓN: EL RADAR ASIMÉTRICO
Actualmente, el sistema Trifásico está altamente amarrado al movimiento macro de **Bitcoin (BTC)**. Esto es ideal para el fondo base, pero deja afuera las "anomalías individuales".
El objetivo de este nuevo desarrollo es crear un entorno de **medición milimétrica aislada** para cada moneda.

### ¿Qué medirá este Radar?
- **Z-Score Individual:** Cuántas desviaciones estándar se ha movido el precio de una moneda respecto a su propia media en 1m y 5m.
- **Micro-Sustos (Drops Anormales):** Detectar cuándo una moneda sufre una caída masiva de liquidez sin que BTC se haya movido. Ej: ETH cae 5% y BTC 0.2%.
- **Separación del Ruido:** Diferenciar una caída de -4% en Ethereum (grave) vs una caída de -4% en WIF (ruido normal) evaluando percentiles estadísticos pasados.

---

## 2. ARQUITECTURA DEL SISTEMA PARA 24GB

Al contar con 24GB de RAM en OCI, dejaremos de operar 8 pares conservadores y apuntaremos al espectro amplio.

1. **Universo de Análisis:** Top 100/150 monedas en Binance (las que tengan volumen consolidado y superen filtros de spreads).
2. **"Data Layer" Puramente Cuantitativa:** Una estrategia de Freqtrade que NO opera, sino que usa `.sqlite3` para recopilar distribuciones de probabilidad en vivo de cada moneda.
3. **Pistola de Mean-Reversion:** Una vez medidas las monedas, se activa un bot paralelo con un capital separado que entra *exclusivamente* cuando detecta las anomalías identificadas. Compra el pánico infundado y vende en el rebote instintivo a los pocos minutos.

---

## 3. PASOS DE DESARROLLO (PRE-24GB)
*Mientras esperamos la instancia, el trabajo de desarrollo local consistirá en:*

- [ ] **Creación del Bot Radar (Dry-Run):** Programar la lógica de análisis estadístico en Python (ATR Normalizado, Volatilidad Absoluta).
- [ ] **Base de Datos de Umbrales:** Un registro temporal para ver qué significa un "susto real" para cada moneda (umbral dinámico vs estático).
- [ ] **Backtesting Aislado:** Probar la lógica de rebote rápido en el histórico de 2024 para las top altcoins confirmando WinRates > 75% en entradas de "Susto".

---
*Este documento queda fijo como meta de fin de año 2026. Prioridad actual: Validación total de seguridad y estabilidad del Trifásico.*
