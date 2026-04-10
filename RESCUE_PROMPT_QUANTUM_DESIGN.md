# 🦅 PROMPT DE ARQUITECTURA CUÁNTICA: EL FINO DE LA LATERALIDAD

**COPIA Y PEGA ESTO A UNA IA DE ALTO NIVEL (DeepSeek-V3, Claude 3.5 Opus/Sonnet, GPT-4o)**

---

**Actúa como un Senior Quantum Trader y Desarrollador Full-Stack especializado en Freqtrade.**

## 1. EL DESAFÍO: ESTRATEGIA CHACAL LATERAL V4
Tengo una estrategia de reversión a la media (Mean Reversion) para mercados laterales que es **altamente rentable en su núcleo (+10% mensual, 82% WinRate)** pero falla catastróficamente al intentar "afinar" las entradas y salidas con temporalidades micro (1m).

### El Núcleo (Lo que funciona - DNA 62):
- **Timeframe:** 5m para ejecución, 1h para Macro.
- **Lógica:** Comprar en Bollinger Band Lower (2.0) y Vender en Bollinger Band Upper.
- **Salida Maestra (TARGET_MID):** Cerramos en la media de Bollinger (`bb_mid`) siempre que el profit sea > 0. Esto garantiza que no nos quedemos "atrapados" esperando una reversión completa que nunca llega.
- **Filtro Macro:** Solo operamos si BTC/USDT (1h) está ±3.9% de su EMA50.

## 2. EL PROBLEMA: EL "PICADILLO" DE 1 MINUTO
Intentamos usar el RSI de 1m para evitar "atrapar cuchillos". 
- **Setup:** Si el precio toca la banda baja de 5m, NO entramos hasta que el RSI_1m sea < 25.
- **Resultado:** El bot se vuelve "asustadizo". Las mechas (wicks) de 1m generan señales falsas que hacen que el bot entre tarde o salga en pánico antes de que la lógica de 5m complete su ciclo. El 1m está actuando como un "Gatillo Binario" ruidoso en lugar de una "Mira de Precisión".

## 3. LO QUE NECESITO QUE DISEÑES
No quiero que me des un código genérico. Quiero una re-ingeniería de la **Mira de 1 Minuto**:

1.  **Entrada "Sniper" (1m):** En lugar de un RSI estricto, diseña una lógica que detecte **Agotamiento de Tendencia Micro**. (Ej: Divergencias RSI/Precio en 1m, o un "Price Action" simple como: "Entrar solo si la vela de 1m cierra por encima del máximo de la vela anterior tras tocar la banda de 5m").
2.  **Salida "Airbag" (Security 1m):** Una lógica que nos saque de un trade lateral solo si hay una **Ruptura Real (Breakout)** y no una simple mecha de volatilidad. ¿Cómo diferenciamos una liquidación de cortos (mecha) de un cambio de tendencia real en 1m?
3.  **Filtrado de Ruido institucional:** Implementa un sistema de **Scoring**. Que el 1m no sea un `if/else`, sino un valor que sume puntos a la probabilidad de éxito.

## 4. CONTEXTO TÉCNICO
- Framework: `Freqtrade` (Python).
- Librería: `ta-lib`.
- Debes usar `informative_pairs` para traer los datos de 1m y 1h sin causar "Lookahead bias".

**Instrucción de tu respuesta:**
- Presenta la teoría de por qué el 1m está rompiendo la rentabilidad actual.
- Proporciona el código de `populate_indicators`, `populate_entry_trend` y `populate_exit_trend` implementando estas mejoras.
- Asegúrate de que el código sea compatible con el modo **Futures** (Short y Long).

---
