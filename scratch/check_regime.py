import requests
import pandas as pd
import numpy as np

def get_btc_data():
    try:
        url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=100"
        response = requests.get(url, timeout=10)
        data = response.json()
        df = pd.DataFrame(data, columns=['time','open','high','low','close','vol','close_time','q_vol','trades','take_base','take_quote','ignore'])
        df['close'] = df['close'].astype(float)
        return df
    except Exception as e:
        print(f"Error API Binance: {e}")
        return None

df = get_btc_data()
if df is not None:
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    last_price = df['close'].iloc[-1]
    last_ema = df['ema50'].iloc[-1]
    diff_pct = (last_price / last_ema) - 1
    print(f"BTC Price: {last_price}")
    print(f"EMA50 (1h): {last_ema}")
    print(f"Diff %: {round(diff_pct * 100, 2)}%")
    
    threshold = 0.043
    if abs(diff_pct) < threshold:
        print("Regime: LATERAL")
    elif diff_pct > threshold:
        print("Regime: BULL")
    else:
        print("Regime: BEAR")
