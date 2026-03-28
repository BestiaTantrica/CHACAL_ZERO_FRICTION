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