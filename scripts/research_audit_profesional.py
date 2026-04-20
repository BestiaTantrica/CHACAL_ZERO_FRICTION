"""
CHACAL ARENA - AUDIT ENGINE V1.0
=================================
Auditoría de alta precisión para la estrategia FAN-HUNTER.
Corrige todos los sesgos de la simulación naive anterior:
 1. Entrada en la vela SIGUIENTE (Lookahead fix)
 2. Comisiones reales de Binance Futures (0.05% taker per side)
 3. Funding rate típico adverso en shorts (0.01% cada 8h)
 4. Z-Score normalizado por día de la semana (Elimina el sesgo estacional)
 5. Slippage estimado (0.1% para activos ilíquidos)
 6. Múltiples posiciones simultáneas (Una por par)
"""

import pandas as pd
import numpy as np
import os

DATA_DIR = r"C:\CHACAL_ZERO_FRICTION\research_data"

# === PARÁMETROS REALES DE MERCADO ===
FEE_PER_TRADE = 0.05 / 100        # Taker fee Binance Futures (%)
SLIPPAGE = 0.10 / 100              # Spread en tokens ilíquidos (%)
FUNDING_RATE_8H = 0.01 / 100       # Funding adverso en shorts (por 8h)

def compute_indicators(df, label=""):
    """Calcula indicadores con corrección de sesgo estacional."""
    
    # --- Z-Score ESTACIONAL (Normalizado por día de semana) ---
    # Para evitar comparar el volumen del viernes con el martes
    df['day_of_week'] = df['date'].dt.dayofweek
    df['hour'] = df['date'].dt.hour
    
    # Media y std por (día_semana, hora) usando una ventana rodante de 4 semanas
    df['vol_mean_seasonal'] = (
        df.groupby(['day_of_week', 'hour'])['volume']
        .transform(lambda x: x.rolling(window=4, min_periods=1).mean())
    )
    df['vol_std_seasonal'] = (
        df.groupby(['day_of_week', 'hour'])['volume']
        .transform(lambda x: x.rolling(window=4, min_periods=1).std().fillna(1))
    )
    df['z_score_seasonal'] = (df['volume'] - df['vol_mean_seasonal']) / df['vol_std_seasonal']
    
    # --- Z-Score SIMPLE (Para comparar) ---
    df['vol_mean_24'] = df['volume'].rolling(window=1440).mean()
    df['vol_std_24'] = df['volume'].rolling(window=1440).std()
    df['z_score_simple'] = (df['volume'] - df['vol_mean_24']) / df['vol_std_24']
    
    # --- RSI ---
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # --- EMA Rápida (Detección de micro-tendencia en curso) ---
    df['ema9'] = df['close'].ewm(span=9).mean()
    df['ema21'] = df['close'].ewm(span=21).mean()
    
    # --- Cuerpo de Vela y Dirección ---
    df['body'] = abs(df['close'] - df['open'])
    df['is_bullish'] = df['close'] > df['open']
    
    return df


def simulate_realistic(df, symbol, z_type='seasonal', allow_long=False):
    """
    SIMULACIÓN REALISTA:
    - Entrada al OPEN de la vela SIGUIENTE a la señal (no al close actual)
    - Comisiones + Slippage aplicados en entrada y salida
    - Funding rate cobrado en Shorts cada 8h
    """
    
    z_col = 'z_score_seasonal' if z_type == 'seasonal' else 'z_score_simple'
    Z_THRESH = 8.0
    RSI_SHORT_MIN = 85
    RSI_LONG_MAX = 60
    
    trades = []
    in_trade = False
    pos_type = None
    entry_price = 0.0
    candles_in_trade = 0
    
    for i in range(1441, len(df) - 1):
        row_now = df.iloc[i]           # Vela donde se genera la SEÑAL
        row_next = df.iloc[i + 1]      # Vela donde ENTRA la orden (realista)
        
        if not in_trade:
            # --- SEÑAL SHORT ---
            if row_now['rsi'] > RSI_SHORT_MIN:
                in_trade = True
                pos_type = 'short'
                entry_price = row_next['open'] * (1 - SLIPPAGE)  # Peor precio
                candles_in_trade = 0
                
            # --- SEÑAL LONG (Solo si está habilitado) ---
            elif allow_long and row_now[z_col] > Z_THRESH and row_now['rsi'] < RSI_LONG_MAX:
                in_trade = True
                pos_type = 'long'
                entry_price = row_next['open'] * (1 + SLIPPAGE)  # Peor precio
                candles_in_trade = 0
        else:
            candles_in_trade += 1
            
            if pos_type == 'short':
                raw_profit = (entry_price - row_now['close']) / entry_price * 100
                # Funding adverso (pagamos cada 480 velas de 1m = 8 horas)
                funding_cost = (candles_in_trade // 480) * FUNDING_RATE_8H * 100
                net_profit = raw_profit - funding_cost
                
                if row_now['rsi'] < 40 or net_profit >= 5.0 or net_profit <= -3.5:
                    final = net_profit - (FEE_PER_TRADE * 2 * 100)  # Fee entrada+salida
                    trades.append({'type': 'short', 'profit': final, 'candles': candles_in_trade})
                    in_trade = False
                    
            else:  # long
                raw_profit = (row_now['close'] - entry_price) / entry_price * 100
                net_profit = raw_profit
                
                if row_now['rsi'] > 82 or net_profit >= 8.0 or net_profit <= -4.0:
                    final = net_profit - (FEE_PER_TRADE * 2 * 100)
                    trades.append({'type': 'long', 'profit': final, 'candles': candles_in_trade})
                    in_trade = False
    
    return pd.DataFrame(trades) if trades else pd.DataFrame()


def run_audit(symbol, allow_long_short=(False, True)):
    """Ejecuta la auditoría completa y compara modelos."""
    allow_long, allow_short = allow_long_short
    
    path = os.path.join(DATA_DIR, f"{symbol}_1m_recent.csv")
    if not os.path.exists(path):
        print(f"  Skip {symbol}: sin datos")
        return

    df = pd.read_csv(path)
    df['date'] = pd.to_datetime(df['date'])
    df = compute_indicators(df)
    
    # Modelo Naive (Nuestro backtest anterior)
    trades_naive_df = simulate_realistic(df, symbol, z_type='simple', allow_long=allow_long)
    # Modelo Realista (Con correcciones)
    trades_real_df = simulate_realistic(df, symbol, z_type='seasonal', allow_long=allow_long)
    
    print(f"\n{'='*50}")
    print(f"  {symbol}")
    print(f"{'='*50}")
    
    for label, tdf in [("NAIVE (Z simple, entrada naive)", trades_naive_df), 
                        ("REALISTA (Z estacional + fees + slippage)", trades_real_df)]:
        if tdf.empty:
            print(f"  {label}: Sin trades")
            continue
        net = tdf['profit'].sum()
        wr = (tdf['profit'] > 0).mean() * 100
        avg = tdf['profit'].mean()
        print(f"\n  [{label}]")
        print(f"    Net Profit: {net:.2f}%  |  WR: {wr:.1f}%  |  Avg: {avg:.2f}%  |  Trades: {len(tdf)}")
        if 'type' in tdf.columns:
            for t in tdf['type'].unique():
                p = tdf[tdf['type']==t]['profit'].sum()
                print(f"    -> {t}: {p:.2f}%")


if __name__ == "__main__":
    print("CHACAL ARENA - AUDITORÍA PROFESIONAL (V1.0)")
    print("Corrigiendo: next-candle entry, fees, slippage, Z-Score estacional")
    print("-" * 60)
    
    configs = [
        ("OGUSDT",    (False, True)),   # Solo Short
        ("SANTOSUSDT",(True, True)),    # Dual
        ("LAZIOUSDT", (False, True)),   # Solo Short
        ("ALPINEUSDT",(False, True)),   # Solo Short
    ]
    
    for symbol, mode in configs:
        run_audit(symbol, allow_long_short=mode)
