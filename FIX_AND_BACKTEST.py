"""
CHACAL ZERO FRICTION — Script de Emergencia
Hace 2 cosas:
1. Renombra todos los archivos con _USDT_USDT a _USDT (si no se hizo antes)
2. Llama a freqtrade backtesting directamente via subprocess
"""
import os
import subprocess
import sys

DATA_DIR = r"C:\CHACAL_ZERO_FRICTION\user_data\data\binance\futures"

# PASO 1: Renombrar archivos si todavia tienen nombre duplicado
print("--- PASO 1: Verificando nombres de archivos ---")
renamed = 0
for fname in os.listdir(DATA_DIR):
    if "_USDT_USDT" in fname:
        old = os.path.join(DATA_DIR, fname)
        new = os.path.join(DATA_DIR, fname.replace("_USDT_USDT", "_USDT"))
        os.rename(old, new)
        print(f"  Renombrado: {fname} -> {fname.replace('_USDT_USDT','_USDT')}")
        renamed += 1

if renamed == 0:
    print("  Archivos ya estan con nombres correctos.")
else:
    print(f"  {renamed} archivos renombrados OK.")

# Verificar que BTC existe
btc_5m = os.path.join(DATA_DIR, "BTC_USDT-5m-futures.json")
if os.path.exists(btc_5m):
    print(f"\nOK: {btc_5m} confirmado.")
else:
    print(f"\nERROR: No encuentro {btc_5m}")
    sys.exit(1)

# PASO 2: Correr el backtest via Docker con la ruta correcta
print("\n--- PASO 2: Lanzando backtest de 60 dias (Abril-Junio 2024) ---")
cmd = [
    "docker", "run", "--rm",
    "-v", r"C:\CHACAL_ZERO_FRICTION\PROJECT_SNIPER_AWS\user_data:/freqtrade/user_data",
    "-v", r"C:\CHACAL_ZERO_FRICTION\user_data\data\binance\futures:/freqtrade/user_data/data/binance/futures",
    "freqtradeorg/freqtrade:stable",
    "backtesting",
    "--config", "/freqtrade/user_data/configs/config_backtest_bear_1m.json",
    "--strategy", "ChacalSniper_Bear_ULTRA",
    "--timerange", "20240402-20240601",
    "--timeframe", "5m",
]

print("Ejecutando:", " ".join(cmd))
result = subprocess.run(cmd, capture_output=False, text=True)
print("\nCodigo de salida:", result.returncode)
