import ccxt
import time

def get_market_regime():
    try:
        exchange = ccxt.binance({'options': {'defaultType': 'future'}})
        # Get 1h candles
        ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=100)
        closes = [candle[4] for candle in ohlcv]
        last_price = closes[-1]
        
        # Simple EMA50 calculation
        ema_period = 50
        ema = sum(closes[:ema_period]) / ema_period # Start with SMA
        multiplier = 2 / (ema_period + 1)
        for price in closes[ema_period:]:
            ema = (price - ema) * multiplier + ema
        
        diff = (last_price / ema) - 1
        
        print(f"BTC Price: ${last_price:.2f}")
        print(f"BTC EMA50 (1h): ${ema:.2f}")
        print(f"Difference: {diff*100:.2f}%")
        
        if diff < 0:
            print("REGIME: BEAR (BTC < EMA50)")
        elif diff > 0.043:
            print("REGIME: BULL (BTC > EMA50 + 4.3%)")
        else:
            print("REGIME: LATERAL (Standard Zone)")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_market_regime()
