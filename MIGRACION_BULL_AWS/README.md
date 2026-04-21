# 🦊 MIGRACIÓN BULL AWS (Elite V2.0)
## Propósito: Operación solo LONG en mercados alcistas (Pumps).

### Composición del Módulo:
- **Estrategia:** `ChacalVolumeHunter_V5.py` (Agresiva FOMO, leverage 10x).
- **Timeframe:** 1m (Gatillo rápido) / 1h (Marco Macro).
- **Config:** `user_data/configs/config.json`.

### Cómo operar en AWS (Nativo):
1. Copiar esta carpeta a la instancia AWS.
2. Ejecutar comando simple:
   ```bash
   freqtrade trade --config user_data/configs/config.json --strategy ChacalVolumeHunter_V5 --strategy-path user_data/strategies
   ```

### Reglas de Uso Manuel:
- Activar SOLO cuando BTC > EMA50 + 4.3% (o tendencia Bull clara).
- No correr en la misma instancia que el bot BEAR.
