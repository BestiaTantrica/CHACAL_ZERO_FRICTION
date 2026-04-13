#!/usr/bin/env python3
"""
AUDITOR V2 - Simula el Backtest vs Live para encontrar la discrepancia exacta
"""
import sys
sys.path.insert(0, '/home/ubuntu/chacal/.venv/lib/python3.12/site-packages')

import ccxt
import pandas as pd
import talib

exchange = ccxt.binance({'options': {'defaultType': 'future'}})

# BTC 1h
btc_1h = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=200)
df_btc = pd.DataFrame(btc_1h, columns=['ts','open','high','low','close','volume'])
df_btc['ema50'] = talib.EMA(df_btc['close'], timeperiod=50)
df_btc['atr'] = talib.ATR(df_btc['high'], df_btc['low'], df_btc['close'], timeperiod=14)
df_btc['atr_mean'] = df_btc['atr'].rolling(8).mean()
last = df_btc.iloc[-1]

btc_trend_bear = last['close'] < last['ema50']
btc_vol_active = last['atr'] > last['atr_mean']
master_switch_ACTUAL = int(btc_trend_bear and btc_vol_active)  # Lo que hace el bot HOY
master_switch_FAILSAFE = 1  # Lo que hacia el bot en el BACKTEST (cuando BTC data no cargaba)

print("=" * 65)
print("SIMULACION: BACKTEST vs LIVE")
print("=" * 65)
print(f"BTC Price:      ${last['close']:.2f}")
print(f"BTC EMA50:      ${last['ema50']:.2f}")
print(f"Diferencia BTC: {((last['close']/last['ema50'])-1)*100:.2f}%")
print()
print("--- CONDICION DEL master_bear_switch ---")
print(f"BTC < EMA50 (btc_trend_bear):  {btc_trend_bear}")
print(f"ATR activo  (btc_vol_active):  {btc_vol_active}")
print()
print(f"[MODO LIVE HOY]      master_bear_switch = {master_switch_ACTUAL}  <- Bot BLOQUEADO")
print(f"[MODO BACKTEST]      master_bear_switch = {master_switch_FAILSAFE}  <- Bot LIBRE")
print()
print("=" * 65)
print("HIPOTESIS: En el backtest, los informative_pairs de BTC/1h")
print("NO cargaban correctamente con el historico de datos, por lo")
print("que el else (Fail-safe = 1) se activaba SIEMPRE.")
print("El bot operaba SIN el filtro macro de BTC.")
print("En LIVE, BTC 1h carga perfecto y el filtro BLOQUEA todo.")
print("=" * 65)
print()

# Cuantas de las ultimas 200 horas hubieran bloqueado con el filtro actual
horas_bloqueadas = 0
horas_libres = 0
for idx, row in df_btc.iterrows():
    if idx < 10:
        continue
    atr_mean = df_btc['atr'].iloc[max(0,idx-8):idx].mean()
    trend_bear = row['close'] < row['ema50']
    vol_active = row['atr'] > atr_mean
    if trend_bear and vol_active:
        horas_libres += 1
    else:
        horas_bloqueadas += 1

total = horas_libres + horas_bloqueadas
print(f"Ultimas {total} horas historicas:")
print(f"  - Horas con master_switch=1 (bot habria operado): {horas_libres}  ({horas_libres/total*100:.1f}%)")
print(f"  - Horas con master_switch=0 (bot habria estado mudo): {horas_bloqueadas}  ({horas_bloqueadas/total*100:.1f}%)")
print()
print("Si el backtest usaba fail-safe=1 siempre, entonces operaba")
print(f"el {horas_bloqueadas/total*100:.1f}% del tiempo que ahora esta en silencio.")
print()

# Condiciones de entrada SIN el master_switch como filtro
pares = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT', 'AVAX/USDT', 'LINK/USDT', 'DOGE/USDT']
print("=" * 65)
print("CONDICIONES DE ENTRADA SIN master_bear_switch (modo backtest)")
print(f"{'Par':<15} {'RSI':>6} {'ADX':>6} {'Vol>1.44x':>10} {'Chg<-0.1%':>10} {'DISPARO':>8}")
print("-" * 65)

disparos = 0
for par in pares:
    try:
        ohlcv = exchange.fetch_ohlcv(par, '5m', limit=100)
        df = pd.DataFrame(ohlcv, columns=['ts','open','high','low','close','volume'])
        df['adx'] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=14)
        df['rsi'] = talib.RSI(df['close'], timeperiod=14)
        df['vol_mean'] = df['volume'].rolling(20).mean()
        df['price_change'] = (df['close'] - df['open']) / df['open']
        l = df.iloc[-1]
        c2 = l['price_change'] < -0.001
        c3 = l['rsi'] < 32
        c4 = l['adx'] > 26
        c5 = l['volume'] > l['vol_mean'] * 1.44
        combo_sin_master = all([c2,c3,c4,c5])
        if combo_sin_master:
            disparos += 1
        print(f"{par:<15} {l['rsi']:>6.1f} {l['adx']:>6.1f} {'SI' if c5 else 'NO':>10} {'SI' if c2 else 'NO':>10} {'DISPARO!' if combo_sin_master else '---':>8}")
    except Exception as e:
        print(f"{par:<15} ERROR: {e}")

print()
print(f"Pares que DISPARIAN ahora si master_switch fuera 1: {disparos}/8")
