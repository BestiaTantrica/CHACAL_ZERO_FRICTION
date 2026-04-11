import subprocess
import time
import pandas as pd
import numpy as np
import requests
import os

# CONFIGURACIÓN MAESTRA
LATERAL_THRESHOLD = 0.039  # 3.9%
EMA_PERIOD = 50
CHECK_INTERVAL = 60        # Segundos entre chequeos

def get_btc_price_1h():
    """Obtiene datos de BTC/USDT 1h desde la API de Binance"""
    try:
        url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=100"
        response = requests.get(url, timeout=10)
        data = response.json()
        df = pd.DataFrame(data, columns=['time','open','high','low','close','vol','close_time','q_vol','trades','take_base','take_quote','ignore'])
        df['close'] = df['close'].astype(float)
        return df
    except Exception as e:
        print(f"Error cargando BTC: {e}")
        return None

def manage_regime(regime):
    """Controla los servicios systemd según el régimen"""
    services = {
        "MODO_LATERAL": "ft-lateral.service",
        "MODO_BULL": "ft-bull.service",
        "MODO_BEAR": "ft-bear.service"
    }

    active_service = services.get(regime)
    
    for r, svc in services.items():
        if svc == active_service:
            # Encender el que toca
            print(f"-> Activando: {svc} ({r})")
            subprocess.run(["sudo", "systemctl", "start", svc])
        else:
            # Apagar los demás
            subprocess.run(["sudo", "systemctl", "stop", svc])

def main():
    last_regime = None
    print("--- INICIANDO ORQUESTADOR CHACAL TRIFÁSICO ---")

    while True:
        df = get_btc_price_1h()
        if df is not None:
            # Calcular EMA50
            df['ema50'] = df['close'].ewm(span=EMA_PERIOD, adjust=False).mean()
            last_price = df['close'].iloc[-1]
            last_ema = df['ema50'].iloc[-1]
            
            diff_pct = (last_price / last_ema) - 1
            
            # Determinación de Régimen
            if abs(diff_pct) < LATERAL_THRESHOLD:
                regime = "MODO_LATERAL"
            elif diff_pct > 0:
                regime = "MODO_BULL"
            else:
                regime = "MODO_BEAR"

            print(f"[{time.strftime('%H:%M:%S')}] BTC: ${last_price} | EMA50: ${round(last_ema, 2)} | Diff: {round(diff_pct*100, 2)}% | Régimen: {regime}")

            if regime != last_regime:
                print(f"!!! CAMBIO DE RÉGIMEN DETECTADO: {last_regime} -> {regime}")
                manage_regime(regime)
                last_regime = regime
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
