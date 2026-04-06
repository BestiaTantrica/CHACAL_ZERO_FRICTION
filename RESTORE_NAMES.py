"""
RESTAURAR NOMBRES CORRECTOS de archivos de datos de Freqtrade futures.
El formato correcto para BTC/USDT:USDT es BTC_USDT_USDT-5m-futures.json
Yo los renombre mal. Este script los revierte.
"""
import os, re

dirs = [
    r"C:\CHACAL_ZERO_FRICTION\user_data\data\binance\futures",
    r"C:\CHACAL_ZERO_FRICTION\PROJECT_SNIPER_AWS\user_data\data\binance\futures",
]

for d in dirs:
    if not os.path.exists(d):
        print(f"No existe: {d}")
        continue
    print(f"\nProcesando: {d}")
    renamed = 0
    for fname in os.listdir(d):
        # Detectar archivos que tienen solo un _USDT antes del timeframe
        # Patron: ALGO_USDT-Xm-futures.json  (le falta el segundo _USDT)
        # Correcto: ALGO_USDT_USDT-Xm-futures.json
        if re.match(r'.+_USDT-\d+[mhd]-(futures|mark|funding_rate)\.json', fname):
            new_name = fname.replace('_USDT-', '_USDT_USDT-', 1)
            os.rename(os.path.join(d, fname), os.path.join(d, new_name))
            print(f"  OK: {fname} -> {new_name}")
            renamed += 1
    if renamed == 0:
        print("  Archivos ya tienen nombres correctos (o ya estaban bien).")
    else:
        print(f"  {renamed} archivos restaurados.")

print("\nVERIFICACION:")
test = r"C:\CHACAL_ZERO_FRICTION\PROJECT_SNIPER_AWS\user_data\data\binance\futures\BTC_USDT_USDT-5m-futures.json"
print(f"BTC_USDT_USDT-5m-futures.json existe: {os.path.exists(test)}")
