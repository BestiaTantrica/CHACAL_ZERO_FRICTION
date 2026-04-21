# 🦅 MIGRACIÓN BEAR AWS (Elite V2.0)
## Propósito: Operación solo SHORT en mercados bajistas.

### Composición del Módulo:
- **Estrategia:** `ChacalSniper_Bear44.py` (La más estable, +500% ROI hist).
- **Timeframe:** 1m (Gatillo rápido) / 1h (Marco Macro).
- **Config:** `user_data/configs/config.json`.

### Cómo operar en AWS (Nativo):
1. Copiar esta carpeta a la instancia AWS.
2. Asegurarse que el venv esté activo.
3. Ejecutar comando simple:
   ```bash
   freqtrade trade --config user_data/configs/config.json --strategy ChacalSniper_Bear44 --strategy-path user_data/strategies
   ```

### Reglas de Uso Manuel:
- Activar SOLO cuando BTC < EMA50 (1h).
- No correr en la misma instancia que el bot BULL.
