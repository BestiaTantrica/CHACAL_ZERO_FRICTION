# 🦅 PROTOCOLO DE RESCATE ARCHITECTÓNICO — "GRAVEDAD CERO"

**COPIA Y PEGA TODO EL TEXTO A CONTINUACIÓN A LA NUEVA IA (Ej. Claude 3.5 Sonnet, GPT-4o, DeepSeek Coder):**

***

**Actúa como un Ingeniero DevOps de Nivel Staff y Arquitecto Algorítmico Institucional.**

## 1. CONTEXTO Y OBJETIVO
Soy un trader algorítmico institucional desarrollando el ecosistema **CHACAL ZERO FRICTION** usando **Freqtrade**. Mi objetivo es puramente el análisis de mercado e investigación cuantitativa (diseño de lógicas, selectores de régimen de mercado, mitigación de Drawdown). 

Necesito que diseñes un **entorno de desarrollo e infraestructura espectacular, a prueba de tontos y 100% "sin fricción técnica"**. 
Actualmente estoy bloqueado intentando que el bot reconozca los mercados mediante estrategias dinámicas (cambio de estrategias) porque la infraestructura local nos arruina el avance. 

## 2. EL PROBLEMA (POR QUÉ FALLAMOS)
He perdido días enteros lidiando con "mierda técnica" periférica en lugar de hacer trading cuantitativo por una mezcla tóxica de entornos:
- **Hibridación Windows / Linux:** Uso Windows, Freqtrade es nativo de Linux. El cruce entre PowerShell, WSL2 y Docker originó errores catastróficos.
- **Docker Mounts:** Los montajes de volúmenes compartidos corrompieron las bases `.sqlite`, causaron permisos denegados, problemas de caché, e incluso Docker generó *carpetas fantasmas* en lugar de archivos `.py` por fallos de montaje.
- **Rutas y Datas:** Falla eterna con Freqtrade al no encontrar las rutas correctas (`user_data/data/futures/`) porque se pierde el contexto de ejecución. Error constante: `No history for BTC/USDT found`. Estamos tipear comandos con 15 banderas manualmente en la consola cada vez.
- **Desorden Multi-Estrategia:** Intentamos consolidar un "Triple Mode" (Bull, Bear, Lateral) en un solo archivo antes de tener un motor de ejecución estable.

## 3. LO QUE NECESITO QUE DISEÑES
No voy a tocar un solo comando más de Docker Desktop. Elimínalo de tu plan local. Necesito:

1. **La Estructura de Directorios Definitiva e Incorruptible:** Una morfología de carpetas donde haya una "Madre Nodriza" y subcarpetas lógicas para `scripts/`, `strategies/`, `user_data/data/`.
2. **Entorno Nativo Limpio (Linux/WSL puro):** Define cómo configurar VSCode para que abra directamente dentro del entorno Linux (Dev Environments o un `venv` estricto en WSL) de forma transparente. Cero cmd.exe desde el exterior.
3. **Control por "Scripts Botón Rojo" (Taskfile, Makefile o Bash puro):** Prohíbeme tipear comandos largos. Quiero que escribas 4 o 5 scripts (`.sh` o `Makefile`) que yo ejecute en consola con una sola palabra:
   - `make download-data` (se asegura de bajar 1m, 5m, 1h en futuros SIEMPRE en la ruta perfecta).
   - `make backtest-bear` (corre la validación sobre Agosto aislado).
   - `make hyperopt-bear` 
4. **Metodología de Desarrollo Institucional:** Un pipeline claro sobre cómo debo desarrollar mis estrategias "Bear" y "Bull" separadas antes de que, en un futuro, construyamos el "Meta-Selector" que integre a todas. 

## 4. INVENTARIO ACTUAL
Tenemos esto como base (asume que los archivos `.py` contienen lógicas pesadas y complejas probadas):
- **Estrategia Bear (ChacalSniper_Bear_ULTRA.py):** Mercado bajista. Sólo short. Falló al quedarse trabada pidiendo datos de `5m`.
- **Estrategia Bull (ChacalVolumeHunter_V1.py):** Mercado alcista/lateral. 
- **Timeframes requeridos SIEMPRE:** Necesitamos 1h para macro, 5m para el trade, 1m para Kill Switches. Operamos 100% Futuros Binance.

## Instrucción de tu primera respuesta:
1. Dame un análisis crítico de 2 párrafos de por qué mi ecosistema viejo (Windows+Docker local+mounts) es la peor práctica para Data Science local.
2. Preséntame el árbol de carpetas exacto de la "Arquitectura Definitiva".
3. Escribe el contenido del archivo `Makefile` o un script maestro unificado en bash con los comandos absolutos que encapsularán toda la complejidad técnica para no volver a escribir un argumento `--datadir` en mi vida.
***
