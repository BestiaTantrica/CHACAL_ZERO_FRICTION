"""
ANALIZADOR HISTÓRICO DE CICLOS POR FIN DE SEMANA
=================================================
Descarga los últimos 6 meses en 1h para cada token del cuarteto
y evalúa el rendimiento de la estrategia V4 en CADA fin de semana
individualmente, para detectar:
  1. Consistencia: ¿Siempre gana los fines de semana o fue un outlier?
  2. Asimetría de calendario: ¿Hay fines de semana mejores que otros?
  3. Ciclos dominantes: ¿Cuántas semanas seguidas positivas tiene cada token?
"""
import pandas as pd
import numpy as np
import requests
import time
import os
from datetime import datetime, timedelta

DATA_DIR = r"C:\CHACAL_ZERO_FRICTION\research_data"
BASE_URL = "https://api.binance.com/api/v3/klines"

# Cuarteto definitivo y su modo de operación
CUARTET = {
    "OGUSDT":  {"allow_long": False, "label": "Solo Short"},
    "BARUSDT": {"allow_long": True,  "label": "Dual"},
    "WIFUSDT": {"allow_long": False, "label": "Solo Short"},
    "APEUSDT": {"allow_long": True,  "label": "Dual"},
}

# ─── Descarga ─────────────────────────────────────────────────────────────────
def download_1h(symbol, days=180):
    """Descarga historial completo en 1h de los últimos N días."""
    cache_file = os.path.join(DATA_DIR, f"{symbol}_1h_cycle.csv")
    if os.path.exists(cache_file):
        df = pd.read_csv(cache_file)
        df['date'] = pd.to_datetime(df['date'])
        # Si el cache tiene menos de 24h de antigüedad, reutilizarlo
        if (pd.Timestamp.now() - df['date'].max()).total_seconds() < 86400:
            print(f"  [{symbol}] Usando cache 1h.")
            return df

    print(f"  [{symbol}] Descargando {days}d en 1h...")
    start_ts = int((time.time() - days * 86400) * 1000)
    full_data, last_ts = [], start_ts

    while True:
        params = {"symbol": symbol, "interval": "1h", "startTime": last_ts, "limit": 1000}
        try:
            resp = requests.get(BASE_URL, params=params, timeout=15)
            data = resp.json() if resp.status_code == 200 else []
        except:
            data = []
        if not data:
            break
        full_data.extend(data)
        last_ts = data[-1][0] + 1
        if len(data) < 1000:
            break
        time.sleep(0.1)

    if not full_data:
        return pd.DataFrame()

    df = pd.DataFrame(full_data, columns=[
        'timestamp','open','high','low','close','volume',
        'close_time','qav','nt','tbbav','tbqav','ignore'
    ])
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
    for c in ['open','high','low','close','volume']:
        df[c] = df[c].astype(float)
    df.to_csv(cache_file, index=False)
    return df

def download_1m_window(symbol, start_dt, end_dt):
    """Descarga velas 1m para una ventana específica (máx ~10 días)."""
    start_ts = int(start_dt.timestamp() * 1000)
    end_ts   = int(end_dt.timestamp() * 1000)
    full_data, last_ts = [], start_ts

    while True:
        params = {"symbol": symbol, "interval": "1m",
                  "startTime": last_ts, "endTime": end_ts, "limit": 1000}
        try:
            resp = requests.get(BASE_URL, params=params, timeout=15)
            data = resp.json() if resp.status_code == 200 else []
        except:
            data = []
        if not data:
            break
        full_data.extend(data)
        last_ts = data[-1][0] + 1
        if len(data) < 1000 or last_ts >= end_ts:
            break
        time.sleep(0.08)

    if not full_data:
        return pd.DataFrame()

    df = pd.DataFrame(full_data, columns=[
        'timestamp','open','high','low','close','volume',
        'close_time','qav','nt','tbbav','tbqav','ignore'
    ])
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
    for c in ['open','high','low','close','volume']:
        df[c] = df[c].astype(float)
    return df

# ─── Estrategia V4 ────────────────────────────────────────────────────────────
def run_v4(df, allow_long=True):
    """Simula la estrategia V4 sobre un DataFrame de 1m con warmup previo."""
    if len(df) < 1500:
        return {"net": 0, "trades": 0, "wins": 0}

    df = df.copy().reset_index(drop=True)
    df['vol_mean'] = df['volume'].rolling(1440).mean()
    df['vol_std']  = df['volume'].rolling(1440).std()
    df['z_score']  = (df['volume'] - df['vol_mean']) / df['vol_std']

    delta = df['close'].diff()
    gain  = delta.where(delta > 0, 0).rolling(14).mean()
    loss  = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['rsi'] = 100 - (100 / (1 + gain / loss))

    Z_THRESHOLD   = 10.0
    RSI_ENTRY_MAX = 65
    RSI_SHORT_MIN = 88

    in_pos = False
    pos_type = None
    entry_price = 0
    trades = []

    for i in range(1440, len(df)):
        row = df.iloc[i]
        if not in_pos:
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
        return {"net": 0, "trades": 0, "wins": 0}
    return {
        "net":    sum(trades),
        "trades": len(trades),
        "wins":   sum(1 for t in trades if t > 0),
    }

# ─── Identificar fines de semana ─────────────────────────────────────────────
def get_weekend_windows(weeks_back=12):
    """
    Genera pares (inicio, fin) para cada fin de semana.
    Inicio = Viernes a las 00:00 UTC
    Fin    = Lunes a las 08:00 UTC (permite cierre de posiciones abiertas)
    Necesitamos 1 día extra de warmup ANTES del inicio para los indicadores.
    """
    windows = []
    # Encontrar el último viernes UTC pasado
    now = datetime.utcnow()
    # weekday: 0=Lun, 4=Vie, 5=Sab, 6=Dom
    days_since_fri = (now.weekday() - 4) % 7
    last_friday = now - timedelta(days=days_since_fri)
    last_friday = last_friday.replace(hour=0, minute=0, second=0, microsecond=0)

    for i in range(weeks_back):
        fri = last_friday - timedelta(weeks=i)
        mon = fri + timedelta(days=3, hours=8)  # Lunes 08:00
        warmup_start = fri - timedelta(days=1)  # Jueves 00:00 — warmup 1m
        windows.append({
            "week":         i + 1,
            "fri":          fri,
            "mon":          mon,
            "warmup_start": warmup_start,
            "label":        fri.strftime("%d %b %Y"),
        })
    return windows

# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    windows = get_weekend_windows(weeks_back=12)
    results = {}  # {symbol: [{week, label, net, trades, winrate}]}

    for symbol, cfg in CUARTET.items():
        print(f"\n{'='*60}")
        print(f"ANALIZANDO: {symbol} ({cfg['label']})")
        print(f"{'='*60}")
        symbol_results = []

        for w in windows:
            print(f"  Semana {w['week']:>2}: {w['label']} ... ", end="", flush=True)
            df = download_1m_window(symbol, w['warmup_start'], w['mon'])

            if df.empty or len(df) < 1500:
                print(f"Sin datos suficientes.")
                symbol_results.append({
                    "week": w['week'], "label": w['label'],
                    "net": None, "trades": 0, "winrate": None
                })
                continue

            # Filtramos para analizar SOLO los trades iniciados desde el viernes
            res = run_v4(df, allow_long=cfg['allow_long'])
            wr  = (res['wins'] / res['trades'] * 100) if res['trades'] > 0 else 0
            flag = "✅" if res['net'] >= 5.0 else ("⚠️" if res['net'] > 0 else "❌")
            print(f"{flag} Net: {res['net']:+.2f}%  WinRate: {wr:.0f}% ({res['trades']} trades)")

            symbol_results.append({
                "week":    w['week'],
                "label":   w['label'],
                "net":     res['net'],
                "trades":  res['trades'],
                "winrate": wr,
            })

        results[symbol] = symbol_results

    # ─── Reporte final ────────────────────────────────────────────────────────
    print(f"\n\n{'='*70}")
    print("RESUMEN HISTÓRICO — CUARTETO CHACAL FAN-HUNTER")
    print(f"{'='*70}")
    print(f"{'Semana (Viernes)':<18}", end="")
    for sym in CUARTET:
        print(f"  {sym:<14}", end="")
    print()
    print("-" * 70)

    all_weeks = windows
    for w in all_weeks:
        print(f"{w['label']:<18}", end="")
        for sym in CUARTET:
            sym_data = next((r for r in results[sym] if r['week'] == w['week']), None)
            if sym_data and sym_data['net'] is not None:
                val = sym_data['net']
                flag = "✅" if val >= 5 else ("⚠️" if val > 0 else "❌")
                print(f"  {flag}{val:+6.2f}%      ", end="")
            else:
                print(f"  {'---':<14}", end="")
        print()

    # Estadísticas por símbolo
    print(f"\n{'ESTADÍSTICAS GLOBALES':^70}")
    print("-" * 70)
    for sym, sym_results in results.items():
        valid = [r for r in sym_results if r['net'] is not None]
        if not valid:
            continue
        nets   = [r['net'] for r in valid]
        pos    = sum(1 for n in nets if n > 0)
        big    = sum(1 for n in nets if n >= 5)
        avg_wr = np.mean([r['winrate'] for r in valid if r['winrate'] is not None])
        print(f"\n  {sym} ({CUARTET[sym]['label']}):")
        print(f"    Semanas positivas:    {pos}/{len(valid)} ({pos/len(valid)*100:.0f}%)")
        print(f"    Semanas >5% (élite):  {big}/{len(valid)} ({big/len(valid)*100:.0f}%)")
        print(f"    Net promedio/semana:  {np.mean(nets):+.2f}%")
        print(f"    Mejor semana:         {max(nets):+.2f}%")
        print(f"    Peor semana:          {min(nets):+.2f}%")
        print(f"    WinRate promedio:     {avg_wr:.1f}%")

    # Guardar CSV
    rows = []
    for sym, sym_results in results.items():
        for r in sym_results:
            rows.append({"symbol": sym, **r})
    out_df = pd.DataFrame(rows)
    out_path = os.path.join(DATA_DIR, "historical_cycles.csv")
    out_df.to_csv(out_path, index=False, encoding='utf-8')
    print(f"\n\nResultados guardados en: {out_path}")

if __name__ == "__main__":
    main()
