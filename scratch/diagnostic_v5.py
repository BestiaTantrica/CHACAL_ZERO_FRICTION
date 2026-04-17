import ccxt
import pandas as pd
import pandas_ta as ta
import numpy as np

exchange = ccxt.binance({'options': {'defaultType': 'swap'}})

def check_v5_conditions(symbol):
    print(f"\nEvaluating {symbol} for Chacal Lateral V5...")
    ohlcv = exchange.fetch_ohlcv(symbol, '1m', limit=150)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    # BB 20 on 5m = BB 100 on 1m
    bb = ta.bbands(df['close'], length=100, std=2.0)
    df['bb_lower'] = bb['BBL_100_2.0']
    df['bb_upper'] = bb['BBU_100_2.0']
    df['bb_mid'] = bb['BBM_100_2.0']
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_mid']
    
    # RSI 1m (14)
    df['rsi_1m'] = ta.rsi(df['close'], length=14)
    
    last = df.iloc[-1]
    
    print(f"  Price: {last['close']}")
    print(f"  BB Lower: {last['bb_lower']:.2f}")
    print(f"  BB Upper: {last['bb_upper']:.2f}")
    print(f"  BB Width: {last['bb_width']*100:.2f}% (Min Required: 1.00%)")
    print(f"  RSI 1m: {last['rsi_1m']:.2f}")
    
    # DNA V5 Logic
    band_proximity = 0.002
    bb_width_min = 0.01
    rsi_long_max = 30
    rsi_short_min = 70
    
    long_trigger = (
        (last['bb_width'] > bb_width_min) and 
        (last['close'] <= last['bb_lower'] * (1 + band_proximity)) and 
        (last['rsi_1m'] < rsi_long_max)
    )
    
    short_trigger = (
        (last['bb_width'] > bb_width_min) and 
        (last['close'] >= last['bb_upper'] * (1 - band_proximity)) and 
        (last['rsi_1m'] > rsi_short_min)
    )
    
    if long_trigger:
        print("  >>> LONG SIGNAL DETECTED <<<")
    elif short_trigger:
        print("  >>> SHORT SIGNAL DETECTED <<<")
    else:
        # Diagnostic
        reasons = []
        if not (last['bb_width'] > bb_width_min): reasons.append(f"BB Width too narrow ({last['bb_width']*100:.2f}% < 1.00%)")
        if not (last['close'] <= last['bb_lower'] * (1 + band_proximity)) and not (last['close'] >= last['bb_upper'] * (1 - band_proximity)):
            reasons.append("Price not touching bands")
        if not (last['rsi_1m'] < rsi_long_max) and not (last['rsi_1m'] > rsi_short_min):
            reasons.append(f"RSI neutral ({last['rsi_1m']:.2f})")
        
        print(f"  Status: No trade. Reasons: {', '.join(reasons)}")

symbols = ["BTC/USDT", "SOL/USDT", "LINK/USDT", "AVAX/USDT"]
for s in symbols:
    try:
        check_v5_conditions(s)
    except Exception as e:
        print(f"Error checking {s}: {e}")
