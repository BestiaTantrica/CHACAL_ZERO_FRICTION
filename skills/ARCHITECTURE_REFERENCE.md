# Chacal Zero Friction - Arquitectura de Referencia

## Actualizado: 2026-03-26

### Enfoque de Adaptabilidad en Transiciones

Este documento ha sido actualizado para reflejar el nuevo paradigma de operación:

**Principios Fundamentales:**
1. **Cero valores fijos**: Todos los parámetros deben ser dinámicos (basados en ATR, volatilidad, o métricas de mercado).
2. **Confirmación multi-fuente**: Las señales short requieren validación local + inter-pares + contexto BTC.
3. **Short como contingencia**: No es el modo base; se activa solo en condiciones extremas de quiebre confirmado.

**Referencia Rápida:**
- Estrategia principal: `Chacal_Adaptive_V3.py`
- Configuración: `user_data/config_pure.json`
- Documentación de estado: `skills/CHACAL_STATE_HANDOVER.md`
- Roadmap: `skills/ROADMAP_V3.md`

**Nota:** Cualquier IA que retome este proyecto debe respetar la regla de cero valores fijos. Si no usa funciones que multipliquen ATR o Divergencia, está violando la regla 1 del servidor.