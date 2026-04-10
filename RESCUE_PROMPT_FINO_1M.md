# 🦅 OPERACIÓN "MIRA LÁSER": INVESTIGACIÓN DEL FINO 1M EN ALGO-TRADING INSTITUCIONAL

> **Propósito:** Prompt de investigación avanzado para IAs Cuantitativas/Especialistas.
> **Misión:** Descubrir cómo el trading algorítmico institucional usa temporalidades micro (1m) para lograr entradas/salidas de altísima precisión ("Sniper") en estrategias de reversión a la media (5m-1h), sin ser engañados por el ruido (wicks/mechas) que causa falsos positivos y "comportamiento asustadizo" (picadillo).

---

## CONTEXTO DEL PROBLEMA (Para la IA Investigadora)

Estamos desarrollando **Lateral Hunter**, un bot de Freqtrade (Python) enfocado en mercados laterales (Consolidación / Rango). 
- **Timeframe Base:** 5 minutos (5m) para detectar toques a las Bandas de Bollinger (Reversión a la media).
- **Timeframe Macro:** 1 hora (1h) para confirmar que el precio está plano frente a la EMA50.
- **Timeframe Micro ("El Fino"):** 1 minuto (1m). 

**El Fracaso Actual:** 
Intentamos usar el RSI de 1m como "Gatillo". Si el bot estaba de cara a un Long (en banda baja de 5m), esperábamos que el RSI_1m estuviera < 15 para comprar, y si caía de 15 estando adentro, vendíamos por pánico. 
**Resultado:** Desastre. El bot entra y sale convulsivamente ("picadillo"). El marco de 1m hace mucho ruido, mechas engañosas y picos de volumen que asustan al bot y lo hacen cerrar en el peor momento (el fondo exacto), logrando un WinRate pobre del 54%. Sin embargo, en pruebas pasadas, empalmar bien el 1m logró rentabilidades astronómicas.

---

## 🎯 LAS PREGUNTAS CLAVE A INVESTIGAR

Instrucciones para la IA: Actúa como un Quant de un Hedge Fund especializado en alta frecuencia. Responde con lógica matemática o pseudo-código aplicable a Freqtrade (Pandas / TA-Lib).

### 1. EL "FINO" DE ENTRADA (La Mira, no el Gatillo)
¿Cómo confirman los Quants que el precio en 1m **ha terminado de caer** en un nivel macro (banda de 5m), en lugar de intentar atrapar el cuchillo cayendo?
- ¿Se usan divergencias (Precio hace bajo más bajo en 1m, pero RSI hace bajo más alto)?
- ¿Se espera un quiebre de Fractal/Estructura en 1m (ej. romper el máximo de las últimas 3 velas de 1m)?
- ¿Se usa el Volumen Delta (CVD) o picos anómalos de volumen en 1m como señal de absorción / agotamiento institucional?

### 2. EL "FINO" DE SALIDA (Aguante vs. Escape Real)
¿Cómo diferenciamos en 1m un "falso quiebre" (mecha caza-liquidez) de un "Breakout real" que destruirá nuestro trade de reversión a la media?
- Si solo miramos indicadores como RSI, salimos en pánico. ¿Deberíamos usar la compresión de Bandas de Bollinger de 1 minuto (Squeeze)?
- ¿Se usa validación de tiempo? (Por ejemplo: "Si el precio rompe el nivel crítico en 1m, esperar X minutos para ver si es un amago, o salir solo si Cierra la vela de 5m)?

### 3. EL ALGORITMO COMPUESTO (Suma de Factores)
El usuario intuye que el 1m no debe ser un interruptor Binario (Gatillo) sino una "Mira" que se suma a la puntuación de entrada. 
Diseña un modelo de *Scoring* donde la condición Macro (1h) y Setup (5m) habiliten el arma, y el 1m aumente el "Score" solo cuando se detecta absorción o divergencia, ejecutando la orden sin dudar y sin re evaluar compulsivamente en cada tick de 1 minuto.

---

## ENTREGABLES ESPERADOS DE LA IA
1.  **3 Lógicas Claras (Entrada/Salida/Filtro de Ruido)** explicadas y justificadas.
2.  **Fragmentos de Código Pandas/Freqtrade** usando `ta-lib` para calcular estas divergencias o absorciones en 1m.
3.  **Filosofía Institucional** de por qué el algoritmo viejo fracasó (diagnóstico técnico del "Choppiness").
