# 📊 CHACAL MASTER ESTADO — TABLERO GLOBAL

> **Última actualización:** 2026-04-08
> **Estado:** Repo en saneamiento. Migración a WSL. Evidencias separadas.

---

## 🚦 ESTADO EN TIEMPO REAL

| Proyecto | Estado | Entorno | Notas |
|----------|--------|---------|-------|
| 🦅 **Sniper Bear** | 🟢 **Foco Único** | WSL Nativo | Confirmado: Base Bear44 histórica correcta no replica +118.1% con dataset actual. Problema de incompatibilidad de datos (falta abril real). |
| 🦊 **Volume Hunter** | ⏸️ Pausado | WSL Nativo | En pausa hasta estabilizar la base Bear. |
| 🔮 **Triple Mode** | ❌ Abortado temporal. | WSL Nativo | Rollback realizado por errores de selectores y superposición de paradas. |

---

## 🔴 BLOQUEOS Y HALLAZGOS CRÍTICOS

1. **Hallazgo Duro Bear44 (2026-04-08):**
   - Se reconstruyó la versión exacta de `ChacalSniper_Bear44.py` (commit `d4ca776`) y JSON Época 46. Se verificó con logs que Freqtrade la cargó.
   - **Resultado actual:** Jun-Jul (-16.41%), Stress actual (efectivo may-ago: -23.05%).
   - **Conclusión:** Descartado el error de versión o código pisado. El problema es la discrepancia de datos históricos (el periodo original de abril no está en el dataset actual) y la activación tardía del macro switch en mayo.

2. **Árbol de Trabajo Sucio:**
   - Hay múltiples archivos no trackeados y versiones experimentales en la raíz. Todo lo posterior al commit `942ac9f` debe ser consolidado y commiteado temáticamente.

---

## 📋 PRÓXIMOS PASOS (PLAN DE ACCIÓN)

1. **Saneamiento del Repositorio:**
   - Separar basura y archivos huérfanos.
   - Commits temáticos (docs, scripts, WSL/Makefile, experimentales) para limpiar el árbol local.

2. **Resolución de Incompatibilidad de Datos:**
   - Investigar mecanismo para conseguir el dataset completo de Abril 2024.
   - Revisar lógica de *master bear switch* para que no tarde en prender o apagar en los meses intermedios como mayo/julio.

3. **Arquitectura No-Fricción en WSL:**
   - Completar transición de todos los lanzamientos de Freqtrade vía `Makefile`.

---
*Para auditorías profundas, ver los archivos en `AUDITORIA_*.md` en cada proyecto respectivo.*
