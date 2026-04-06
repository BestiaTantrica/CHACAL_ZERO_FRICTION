
import pandas as pd
import os

data_path = 'C:/CHACAL_ZERO_FRICTION/CHACAL_VOLUME_HUNTER/user_data/data/binance/futures/'

def analyze_trend():
    btc_file = os.path.join(data_path, 'BTC_USDT_USDT-5m-futures.feather')
    if not os.path.exists(btc_file):
        print(f"No encuentro {btc_file}")
        return

    df = pd.read_feather(btc_file)
    # Freqtrade feather columns are usually: date, open, high, low, close, volume
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M')
    
    monthly_btc = df.groupby('month').agg({'close': ['first', 'last']})
    monthly_btc['change %'] = (monthly_btc[('close', 'last')] / monthly_btc[('close', 'first')] - 1) * 100
    
    print("--- TENDENCIA BTC MENSUAL ---")
    print(monthly_btc['change %'])
    
    # Altcoins
    alt_files = [f for f in os.listdir(data_path) if '-5m-futures.feather' in f and 'BTC' not in f]
    all_alt_changes = []
    
    for f in alt_files:
        adf = pd.read_feather(os.path.join(data_path, f))
        adf['date'] = pd.to_datetime(adf['date'])
        adf['month'] = adf['date'].dt.to_period('M')
        m_alt = adf.groupby('month').agg({'close': ['first', 'last']})
        change = (m_alt[('close', 'last')] / m_alt[('close', 'first')] - 1) * 100
        all_alt_changes.append(change)
        
    if all_alt_changes:
        alt_df = pd.concat(all_alt_changes, axis=1)
        print("\n--- TENDENCIA PROMEDIO ALTCOINS (10 PARES) ---")
        print(alt_df.mean(axis=1))

analyze_trend()
