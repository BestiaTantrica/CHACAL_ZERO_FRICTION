
import ccxt
import pandas as pd
import os
from datetime import datetime, timedelta
import time

# =========================================================================
# CHACAL DOWNLOADER v1.0 (Conexión Directa a Binance Futures)
# =========================================================================

DATA_PATH = r'user_data/data/binance/futures'
exchange = ccxt.binance({'options': {'defaultType': 'future'}})

def download_pair_ohlcv(symbol, timeframe, since_date, until_date):
    print(f"📡 Descargando {symbol} en {timeframe}...")
    
    start_ts = exchange.parse8601(since_date + "T00:00:00Z")
    end_ts = exchange.parse8601(until_date + "T23:59:59Z")
    
    all_ohlcv = []
    current_ts = start_ts
    
    while current_ts < end_ts:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=current_ts, limit=1000)
        if not ohlcv: break
        
        all_ohlcv.extend(ohlcv)
        # Siguiente timestamp es el último + 1 intervalo
        last_ts = ohlcv[-1][0]
        current_ts = last_ts + 1
        
        # Evitar bans de rate limit
        time.sleep(0.1)
        
        # Log de progreso
        dt = datetime.fromtimestamp(last_ts / 1000).strftime('%Y-%m-%d %H:%M')
        print(f"   - Progresando: {dt}", end='\r')

    df = pd.DataFrame(all_ohlcv, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    df['date'] = pd.to_datetime(df['date'], unit='ms', utc=True)
    
    # Filtrar solo el rango pedido
    df = df[df['date'] <= pd.to_datetime(until_date, utc=True)]
    
    # Formato nombre Freqtrade: BTC_USDT_USDT-5m-futures.feather
    pair_name = symbol.replace('/', '_').replace(':', '_')
    filename = f"{pair_name}-{timeframe}-futures.feather"
    full_path = os.path.join(DATA_PATH, filename)
    
    # Asegurar carpeta
    if not os.path.exists(DATA_PATH): os.makedirs(DATA_PATH)
    
    df.to_feather(full_path)
    print(f"\n✅ Guardado: {filename} ({len(df)} velas)")

def download_chacal():
    # Periodos sugeridos: Mayo a Agosto
    start = "2024-05-01"
    end = "2024-08-31"
    
    pares = ["BTC/USDT:USDT", "ETH/USDT:USDT", "SOL/USDT:USDT", "LINK/USDT:USDT", "AVAX/USDT:USDT", "ADA/USDT:USDT", "XRP/USDT:USDT"]
    
    for p in pares:
        # Bajamos 1h para el Radar y 5m para las señales
        download_pair_ohlcv(p, "1h", start, end)
        download_pair_ohlcv(p, "5m", start, end)

if __name__ == "__main__":
    download_chacal()
