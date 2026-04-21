"""
ANALIZADOR DE CICLOS POR DIA DE LA SEMANA
==========================================
Para cada token del cuarteto, descarga 6 meses en 1h y luego
corre la estrategia V4 en velas 1m segmentado por DIA de la semana.

Objetivo: detectar si la estrategia funciona SOLO los fines de semana
o si hay dias de semana igual o mas rentables. Sin asumir nada.
"""
import pandas as pd
import numpy as np
import requests
import time
import os
from datetime import datetime, timedelta
import sys
import io

# Windows UTF-8 fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DATA_DIR = r"C:\CHACAL_ZERO_FRICTION\research_data"
BASE_URL  = "https://api.binance.com/api/v3/klines"

# MEGA-SCAN: Encontrar el TOP 6 definitivo
# Todos tienen Futuros en Binance, todos son tokens de evento/meme/deporte
CUARTET = {
    # -- Fan Tokens (Deportivos) --
    "SANTOSUSDT": {"allow_long": True,  "label": "Dual"},
    "OGUSDT":     {"allow_long": False, "label": "Solo Short"},
    "LAZIOUSDT":  {"allow_long": True,  "label": "Dual"},
    "PSGUSDT":    {"allow_long": True,  "label": "Dual"},
    "ACMUSDT":    {"allow_long": True,  "label": "Dual"},
    "ALPINEUSDT": {"allow_long": True,  "label": "Dual"},
    # -- Meme Coins de alta volatilidad --
    "WIFUSDT":    {"allow_long": False, "label": "Solo Short"},
    "NOTUSDT":    {"allow_long": True,  "label": "Dual"},
    "PEPEUSDT":   {"allow_long": False, "label": "Solo Short"},
    "SHIBUSDT":   {"allow_long": True,  "label": "Dual"},
    "BONKUSDT":   {"allow_long": True,  "label": "Dual"},
    "FLOKIUSDT":  {"allow_long": True,  "label": "Dual"},
    # -- Gaming / NFT Event-Driven --
    "IMXUSDT":    {"allow_long": True,  "label": "Dual"},
    "GALAUSDT":   {"allow_long": True,  "label": "Dual"},
    "YGGUSDT":    {"allow_long": True,  "label": "Dual"},
    "PIXELUSDT":  {"allow_long": True,  "label": "Dual"},
}

DIAS = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]

# ─── Descarga 1m (6 meses, con cache) ─────────────────────────────────────────
def download_1m_full(symbol, days=180):
    cache = os.path.join(DATA_DIR, f"{symbol}_1m_dayofweek.csv")
    if os.path.exists(cache):
        df = pd.read_csv(cache)
        df['date'] = pd.to_datetime(df['date'])
        age_hours = (pd.Timestamp.now() - df['date'].max()).total_seconds() / 3600
        if age_hours < 12:
            print(f"  [{symbol}] Cache OK ({len(df):,} velas, {age_hours:.0f}h de antiguedad)")
            return df

    print(f"  [{symbol}] Descargando {days}d en 1m...")
    start_ts = int((time.time() - days * 86400) * 1000)
    full_data, last_ts = [], start_ts

    while True:
        params = {"symbol": symbol, "interval": "1m", "startTime": last_ts, "limit": 1000}
        try:
            resp = requests.get(BASE_URL, params=params, timeout=15)
            data = resp.json() if resp.status_code == 200 else []
        except Exception as e:
            print(f"Error: {e}")
            data = []
        if not data:
            break
        full_data.extend(data)
        last_ts = data[-1][0] + 1
        if len(data) < 1000:
            break
        time.sleep(0.08)
        if len(full_data) % 50000 == 0:
            print(f"    {len(full_data):,} velas descargadas...")

    df = pd.DataFrame(full_data, columns=[
        'timestamp','open','high','low','close','volume',
        'close_time','qav','nt','tbbav','tbqav','ignore'
    ])
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
    for c in ['open','high','low','close','volume']:
        df[c] = df[c].astype(float)
    df.to_csv(cache, index=False)
    print(f"    Guardado: {len(df):,} velas")
    return df

# ─── Construir indicadores (una sola vez por dataset) ─────────────────────────
def build_indicators(df):
    df = df.copy()
    df['vol_mean'] = df['volume'].rolling(1440).mean()
    df['vol_std']  = df['volume'].rolling(1440).std()
    df['z_score']  = (df['volume'] - df['vol_mean']) / df['vol_std']
    delta = df['close'].diff()
    gain  = delta.where(delta > 0, 0).rolling(14).mean()
    loss  = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['rsi'] = 100 - (100 / (1 + gain / loss))
    df['weekday'] = df['date'].dt.weekday  # 0=Lun, 6=Dom
    return df

# ─── Simulacion V4 filtrada por dia de semana ──────────────────────────────────
def run_v4_by_day(df_with_indicators, target_weekday, allow_long=True):
    """
    Corre la logica V4 pero solo abre posiciones en el target_weekday.
    Las posiciones abiertas se cierran igual aunque cambien de dia.
    """
    Z_THRESHOLD   = 10.0
    RSI_ENTRY_MAX = 65
    RSI_SHORT_MIN = 88

    in_pos = False
    pos_type = None
    entry_price = 0
    trades = []

    df = df_with_indicators
    for i in range(1440, len(df)):
        row = df.iloc[i]
        if pd.isna(row['rsi']) or pd.isna(row['z_score']):
            continue

        if not in_pos:
            # Solo entrar si estamos en el dia objetivo
            if row['weekday'] != target_weekday:
                continue
            if allow_long and row['z_score'] > Z_THRESHOLD and row['rsi'] < RSI_ENTRY_MAX:
                in_pos, pos_type, entry_price = True, 'long', row['close']
            elif row['rsi'] > RSI_SHORT_MIN:
                in_pos, pos_type, entry_price = True, 'short', row['close']
        else:
            if pos_type == 'long':
                profit = (row['close'] - entry_price) / entry_price * 100
                if row['rsi'] > 85 or profit >= 8.0 or profit <= -4.0:
                    trades.append(profit)
                    in_pos = False
            else:
                profit = (entry_price - row['close']) / entry_price * 100
                if row['rsi'] < 45 or profit >= 5.0 or profit <= -3.0:
                    trades.append(profit)
                    in_pos = False

    if not trades:
        return {"net": 0.0, "trades": 0, "winrate": 0.0, "avg": 0.0}

    wins = sum(1 for t in trades if t > 0)
    return {
        "net":     round(sum(trades), 2),
        "trades":  len(trades),
        "winrate": round(wins / len(trades) * 100, 1),
        "avg":     round(sum(trades) / len(trades), 2),
    }

# ─── Main ──────────────────────────────────────────────────────────────────────
def main():
    all_results = {}

    for symbol, cfg in CUARTET.items():
        print(f"\n{'='*60}")
        print(f"DESCARGANDO: {symbol} ({cfg['label']})")
        print(f"{'='*60}")

        df_raw = download_1m_full(symbol, days=180)
        if df_raw.empty:
            print(f"  Sin datos para {symbol}")
            continue

        print(f"  Calculando indicadores...")
        df = build_indicators(df_raw)

        print(f"  Simulando por dia de la semana...")
        symbol_days = {}
        for weekday_idx, day_name in enumerate(DIAS):
            res = run_v4_by_day(df, target_weekday=weekday_idx, allow_long=cfg['allow_long'])
            symbol_days[day_name] = res
            marker = "***" if res['net'] >= 5 else ("+++" if res['net'] > 0 else "---")
            print(f"    {day_name:<12}: {marker} Net={res['net']:+7.2f}% | WR={res['winrate']:.0f}% | {res['trades']} trades | avg={res['avg']:+.2f}%/trade")

        all_results[symbol] = symbol_days

    # ─── Tabla resumen ─────────────────────────────────────────────────────────
    print(f"\n\n{'='*80}")
    print("TABLA MAESTRA: RENTABILIDAD POR DIA DE LA SEMANA (6 MESES)")
    print(f"{'='*80}")
    print(f"{'Dia':<14}", end="")
    for sym in CUARTET:
        print(f"  {sym[:8]:<16}", end="")
    print()
    print("-" * 80)

    for day in DIAS:
        print(f"{day:<14}", end="")
        for sym in CUARTET:
            if sym not in all_results or day not in all_results[sym]:
                print(f"  {'---':<16}", end="")
                continue
            r = all_results[sym][day]
            marker = "[BOOM]" if r['net'] >= 10 else ("[OK]" if r['net'] >= 5 else ("[+]" if r['net'] > 0 else "[-]"))
            print(f"  {marker} {r['net']:+6.1f}%      ", end="")
        print()

    # ─── Top dias por token ────────────────────────────────────────────────────
    print(f"\n{'='*80}")
    print("RANKING DE MEJORES DIAS POR TOKEN")
    print(f"{'='*80}")
    for sym, days_data in all_results.items():
        sorted_days = sorted(days_data.items(), key=lambda x: x[1]['net'], reverse=True)
        print(f"\n  {sym} ({CUARTET[sym]['label']}):")
        for i, (day, r) in enumerate(sorted_days[:4], 1):
            bar = "#" * max(0, int(r['net'] / 2))
            print(f"    #{i} {day:<12}: {r['net']:+7.2f}% | {r['winrate']:.0f}% WR | {r['trades']} trades  {bar}")
        worst = sorted_days[-1]
        print(f"    PEOR -> {worst[0]:<10}: {worst[1]['net']:+7.2f}%")

    # ─── Insight clave: comparacion finde vs semana ────────────────────────────
    print(f"\n{'='*80}")
    print("RESUMEN: FINDE (Sab+Dom) vs SEMANA (Lun a Vie)")
    print(f"{'='*80}")
    for sym, days_data in all_results.items():
        finde = days_data.get("Sabado", {}).get("net", 0) + days_data.get("Domingo", {}).get("net", 0)
        semana = sum(days_data.get(d, {}).get("net", 0) for d in ["Lunes","Martes","Miercoles","Jueves","Viernes"])
        total  = finde + semana
        finde_pct  = (finde  / total * 100) if total != 0 else 0
        semana_pct = (semana / total * 100) if total != 0 else 0
        print(f"\n  {sym}: Total={total:+.1f}%")
        print(f"    Finde (Sab+Dom):   {finde:+.2f}%  ({finde_pct:.0f}% del total)")
        print(f"    Semana (L-V):      {semana:+.2f}%  ({semana_pct:.0f}% del total)")
        if semana > finde:
            print(f"    >>> La SEMANA genera MAS rentabilidad que el finde!")
        else:
            print(f"    >>> El FINDE genera mas rentabilidad (sesgo confirmado)")

    # Guardar
    rows = []
    for sym, days_data in all_results.items():
        for day, r in days_data.items():
            rows.append({"symbol": sym, "dia": day, **r})
    pd.DataFrame(rows).to_csv(
        os.path.join(DATA_DIR, "dayofweek_analysis.csv"),
        index=False, encoding='utf-8'
    )
    print(f"\n\nGuardado en: {DATA_DIR}\\dayofweek_analysis.csv")

if __name__ == "__main__":
    main()
