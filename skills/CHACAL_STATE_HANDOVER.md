# Estado real post V3.2 + Diagnóstico de adaptabilidad

## Resumen consolidado (30d y largo plazo)
- **Colapso por shorts**: 78% de los eventos de colapso en los últimos 30 días fueron generados por señales short activadas, no por longs.
- **Causa raíz identificada**: Sobre-activación del parámetro `SHORT_PIVOT_REBELDE` y validación insuficiente de cambio de régimen (falta de confirmación inter-pares + contexto BTC).

## Principios operativos explícitos
1. **Short = Contingencia**: Solo se activa en condiciones extremas de quiebre confirmado.
2. **Confirmación multi-fuente**:
   - Señal local (pivote short)
   - Señal inter-pares (correlación con altcoins)
   - Contexto BTC (volatilidad/liquidez)
3. **Gestión por par independiente**: Cada par mantiene su estado short/long sin interferencia cruzada.

## Hipótesis para validación
- "Martingala al revés": Ajuste dinámico de parámetros short basados en volatilidad histórica.
- "Migajas de pan": Entradas escalonadas con intervalo ligado a volatilidad (ej: 2% de volatilidad → 5 velas de confirmación).

---

# CHACAL VOLUME HUNTER - ESTADO ACTUAL

## Resumen de misión (2026-04-01)
- **Período BULL identificado**: Sep-Nov 2024 (BTC: +7%, +11%, +37%)
- **Hyperopt ejecutado**: 100 épocas, 38 min, mejor época 90 (+0.71%)
- **Backtests**: -17.44% (mejoró de -22.73% previo)
- **Limitación principal**: Solo BTC/ETH tienen datos para 2024. 28 pares con datos desde Sep 2025.

## Estrategia: ChacalVolumeHunter_V1
- **Base**: Chacal_Adaptive_V3 (AWS logic) adaptada para PC
- **Enfoque**: BULL/LATERAL con volumen real
- **Time guard**: Implementado (06-20 UTC solo)
- **Hyperoptables**: buy, sell, trailing
- **Pares válidos**: 28 con datos desde Sep 2025

## Limitaciones hardware
- **CPU**: i3-4170 (2 núcleos, ~100% en backtest)
- **RAM**: 10GB usable
- **Hyperopt 100 épocas**: ~38 min (28 pares, 30 días)

## Pendientes
- Hyperopt con 28 pares (2-3 semanas, datos Sep 2025+)
- Descargar datos 2024 completos para más pares
- Validar time_guard con backtest
- Actualizar ROADMAP.md con estado actual
