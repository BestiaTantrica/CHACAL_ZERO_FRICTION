# AUDITORÍA CIENTÍFICA: ROLLBACK TRIPLE MODE

> **Fecha:** 2026-04-07
> **Estado:** CERRADO
> **Objetivo:** Auditar el intento de consolidar estrategias Bear, Volume y Lateral en un único `ChacalTripleMode.py`.

## 1. Contexto y Objetivos Previos
El ecosistema manejaba estrategias separadas para Bear (Bear_ULTRA/Bear44) y Bull/Lateral (Volume_V1). El objetivo arquitectónico era unificarlas en una sola estrategia que detecte el macro-entorno dinámicamente usando selectores.

## 2. Implementación Técnica
Se desarrolló `ChacalTripleMode.py` incorporando:
- *Mode Switcher* (Super Bear, Bear, Lateral, Bull).
- Hyperoptización de umbrales en rangos separados.
- Integración teórica de dos lógicas de stop/salida en un mismo archivo.

## 3. Síntomas de Falla Observados
Durante las sesiones de pruebas unitarias sobre Freqtrade en WSL, se registraron:
- Errores graves en la evaluación y superposición de umbrales.
- Conflictos en Freqtrade que arrojaban advertencias/salidas abruptas cuando se pretendían optimizar parámetros de salida que compartían estructura pero lógicas irreconciliables (ej. trailing stops conservadores largos vs salidas nerviosas en short).
- Corrupción lógica de la ventaja competitiva (edge): La IA perdía de vista la calibración atómica de "solo shorts", enredando las condicionales y produciendo falsos positivos.

## 4. Conclusión / Resolución
Se decreta temporalmente abortada la idea del `TripleMode`. 
- **Decisión Ejecutiva:** Regresar la matriz a un estado atómico y simple: Focalizar el 100% de la energía de computo en reparar y aislar `ChacalSniper_Bear_ULTRA.py` (y su contraparte de oro `Bear44`).
- **Archivo Testigo:** Toda variante relacionada quedó relegada o aislada para no interferir en el desarrollo estable. La consolidación macro ocurrirá sólo después de tener un Bear robusto confirmado en los dos mayores crashes del 2024.
