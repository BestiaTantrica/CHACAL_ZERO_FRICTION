import pandas as pd

try:
    df = pd.read_feather(r'c:\ai_trading_agent\PROYECTO_CHACAL_PULSE\user_data\data\binance\futures\BTC_USDT_USDT-1h-futures.feather')
    df['date'] = pd.to_datetime(df['date'])
    df['year_month'] = df['date'].dt.to_period('M')
    
    def gain(x):
        return (x['close'].iloc[-1] - x['open'].iloc[0]) / x['open'].iloc[0] * 100
        
    monthly = df.groupby('year_month').apply(gain).sort_values(ascending=False).head(5)
    print("--- TOP 5 MESES MAS SALVAJES (BTC) ---")
    print(monthly)
except Exception as e:
    print(f"Error: {e}")
