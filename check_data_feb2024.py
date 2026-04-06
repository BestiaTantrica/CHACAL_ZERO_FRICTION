import pandas as pd
import os

pares = ['BTC_USDT_USDT', 'ETH_USDT_USDT', 'SOL_USDT_USDT', 'BNB_USDT_USDT', 'XRP_USDT_USDT', 'AVAX_USDT_USDT', 'LINK_USDT_USDT', 'DOGE_USDT_USDT']
base_path = r'c:\ai_trading_agent\PROYECTO_CHACAL_PULSE\user_data\data\binance\futures'

all_ok = True
print("Revisando disponibilidad de datos para FEBRERO 2024 en los 8 pares núcleo:\n")

for p in pares:
    file_path = os.path.join(base_path, f'{p}-5m-futures.feather')
    if not os.path.exists(file_path):
        print(f"[{p}] ARCHIVO NO ENCONTRADO.")
        all_ok = False
        continue
        
    try:
        df = pd.read_feather(file_path)
        df['date'] = pd.to_datetime(df['date'])
        start_date = df['date'].min()
        end_date = df['date'].max()
        
        # Check if Feb 2024 is in the range
        if start_date <= pd.to_datetime('2024-02-01', utc=True) and end_date >= pd.to_datetime('2024-02-28', utc=True):
            print(f"[{p}] OK: Tiene cobertura para Febrero 2024 (Rango total: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')})")
        else:
            print(f"[{p}] FALTAN DATOS: El rango va de {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}.")
            all_ok = False
    except Exception as e:
        print(f"[{p}] Error de lectura: {e}")

if not all_ok:
    print("\n[!] CUIDADO: Faltan datos para algunos pares. Hay que descargar.")
else:
    print("\n[+] LISTO: Tienes todos los datos necesarios para Febrero 2024. Puedes lanzar.")
