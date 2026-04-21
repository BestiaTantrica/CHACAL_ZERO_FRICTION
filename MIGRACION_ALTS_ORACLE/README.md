# 🏝️ MIGRACIÓN ALTS ORACLE (Triada de la Arena)
## Propósito: Operación en Fan Tokens y Altcoins específicas.

### Composición del Módulo:
- **Estrategias:** `ChacalArena_FanHunter.py` (Pumps) y `ChacalLateral_V5.py`.
- **Timeframe:** 1m.
- **Config:** `user_data/configs/config.json` (Incluye proxy SOCKS5 para Oracle).

### Cómo operar en Oracle Cloud:
1. Copiar esta carpeta a la instancia Oracle.
2. Ejecutar comando simple:
   ```bash
   freqtrade trade --config user_data/configs/config.json --strategy ChacalArena_FanHunter --strategy-path user_data/strategies
   ```

### Reglas:
- Operar en modo Dry Run hasta validar rentabilidad del nuevo cuarteto de tokens.
- Usa el proxy local `127.0.0.1:8118` configurado.
