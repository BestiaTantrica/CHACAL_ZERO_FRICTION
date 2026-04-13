import ccxt
import pandas as pd
import pandas_ta as ta
import json

exchange = ccxt.binance({'options': {'defaultType': 'swap'}})
pairs = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT", "AVAX/USDT", "LINK/USDT", "DOGE/USDT"]

def fetch_data(symbol, timeframe, limit=100):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

market_data = {}

print("Fetching data from Binance...")
for pair in pairs:
    try:
        # Fetch 1h data
        df_1h = fetch_data(pair, '1h', limit=150)
        df_1h['rsi_1h'] = ta.rsi(df_1h['close'], length=14)
        if pair == "BTC/USDT":
            df_1h['ema50_1h'] = ta.ema(df_1h['close'], length=50)
            
        current_1h = df_1h.iloc[-1]
        
        # Fetch 5m data
        df_5m = fetch_data(pair, '5m', limit=50)
        df_5m['rsi_5m'] = ta.rsi(df_5m['close'], length=14)
        current_5m = df_5m.iloc[-1]
        
        # Fetch 1m data for tactical sight (referencing 'sight' concept in rules)
        df_1m = fetch_data(pair, '1m', limit=30)
        df_1m['rsi_1m'] = ta.rsi(df_1m['close'], length=14)
        current_1m = df_1m.iloc[-1]
        
        pair_data = {
            "price": float(current_1h['close']),
            "rsi_1h": float(current_1h['rsi_1h']),
            "rsi_5m": float(current_5m['rsi_5m']),
            "rsi_1m": float(current_1m['rsi_1m']),
        }
        
        if pair == "BTC/USDT":
            ema50 = float(current_1h['ema50_1h'])
            price = float(current_1h['close'])
            distance_from_ema50_pct = ((price - ema50) / ema50) * 100
            pair_data["ema50_1h"] = ema50
            pair_data["distance_ema50_pct"] = distance_from_ema50_pct
            
            # Regime Analysis
            # Lateral < 4.3% limit
            if abs(distance_from_ema50_pct) < 4.3:
                # Need to check volume for UMbral logic
                # Volume vs mean volume
                vol_mean = df_1h.iloc[-24:]['volume'].mean()
                vol_current = current_1h['volume']
                vol_ratio = vol_current / vol_mean
                
                if abs(distance_from_ema50_pct) > 2.1:
                    if vol_ratio > 1.5:
                        regime = "UMBRAL_ANTICIPADO (High Volume) -> Relieve to Specialist"
                    else:
                        regime = "LATERAL_UMBRAL (Low Volume) -> Stay Lateral V4"
                else:
                    regime = "LATERAL_PURO -> Lateral V4 Mando"
            else:
                if distance_from_ema50_pct >= 4.3:
                    regime = "TENDENCIA_BULL -> Fox Volume Hunter"
                else:
                    regime = "TENDENCIA_BEAR -> Sniper Bear"
            
            pair_data["btc_regime_status"] = regime

        market_data[pair] = pair_data
        
    except Exception as e:
        print(f"Error fetching data for {pair}: {e}")

print("---------- DATA DUMP ----------")
print(json.dumps(market_data, indent=4))
