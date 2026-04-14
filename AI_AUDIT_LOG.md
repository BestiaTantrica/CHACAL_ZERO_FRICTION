# 🧠 LOG DE AUDITORÍA Y MEJORAS IA (CLAUDE/GROQ)

> **Misión:** Centralizar toda la inteligencia y sugerencias de mejora de IAs de alto nivel para evitar redundancias y mantener la precisión institucional.

---

## 📅 2026-04-14: AUDITORÍA V5 ELITE (Auditado por Antigravity/Claude 3.5)

### 🔴 MEJORAS IMPLEMENTADAS EN SNIPER BEAR V5
- **Fuzzy Logic (El "Tacto"):** Sustitución de umbrales binarios rígidos por un gradiente de confianza (40% EMA dist, 30% ATR, 30% RSI).
- **Leverage Dinámico (ATR-Based):** 7x (Baja vol) / 5x (Normal) / 3x (Estrés).
- **Airbag 1m Robusto:** Implementación de `body_ratio > 0.6` y persistencia de 3/4 velas para evitar mechas de liquidación.
- **Cache de BTC:** Optimización de memoria cargando BTC una sola vez para todos los pares (Evita OOM en t3.micro).

### 🟠 MEJORAS IMPLEMENTADAS EN VOLUME HUNTER V5
- **Bull Confidence Index:** Gradiente basado en RSI 1h y 5m simultáneo.
- **Optimización RAM:** Reducción de ventanas rolling de 144 a 72 velas.

---

## 📋 BACKLOG DE MEJORAS PENDIENTES (SIN IMPLEMENTAR)

1.  **[Prioridad Media] Filtro de Volumen Z-Score:** Implementar medición milimétrica de volumen por moneda para detectar anomalías institucionales antes del pump.
2.  **[Prioridad Alta] Dashboard Interno:** Crear un visualizador de logs que no consuma RAM para monitorear el "Bear Strength" en tiempo real vía Telegram.
3.  **[Prioridad Militar] Rotación de Secrets Automática:** Mover todos los tokens a variables de entorno para evitar filtraciones en Git.

---

## 🛰️ PROTOCOLO DE DESPLIEGUE FÁCIL (ZERO FRICTION)

Para evitar errores de tokens y comandos manuales, usar el script institucional:
1.  **Ejecutar:** `.\SYNC_TO_AWS.bat` desde la raíz.
2.  **Efecto:** Sube estrategias, sincroniza datos `.feather` y reinicia el bot en AWS automáticamente.
3.  **Seguridad:** El script no toca los archivos `config.json` para no pisar tus API Keys reales en el servidor.
