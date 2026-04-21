import subprocess
import time
import pandas as pd
import numpy as np
import requests
import os
import json

# ================================================================
# 🦅 CHACAL ORCHESTRATOR V4.0 - THE SNIPER KING EDITION (FICT TRIFÁSICO)
# ================================================================

LATERAL_ZONE = 0.02         # ±2% para Lateral V4
TREND_THRESHOLD = 0.043     # 4.3% para Especialistas
EMA_PERIOD = 50
CHECK_INTERVAL = 60        # Chequeo cada minuto

def get_telegram_config():
    """Busca el token y chat_id en múltiples rutas posibles para robustez total"""
    possible_paths = [
        '/home/ubuntu/freqtrade/user_data/configs/config.json',
        '/home/ubuntu/chacal/scripts/config_aws.json',
        'scripts/config_aws.json',
        'config_v5_oracle.json',
        'user_data/configs/config.json'
    ]
    
    for path in possible_paths:
        try:
            if os.path.exists(path):
                with open(path) as f:
                    cfg = json.load(f)
                    if 'telegram' in cfg:
                        return cfg['telegram']['token'], cfg['telegram']['chat_id']
        except:
            continue
            
    # Fallback al token verificado hoy para AWS (Volume Pairs Bot)
    return "8760247299:AAHNhw7k-YlEG2kL7lO0Ze5cbuRzg7y8bW4", "6527908321"

def send_telegram(token, chat_id, message):
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": f"🦅 [CEREBRO SNIPER]: {message}"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def get_btc_data():
    """Obtiene datos frescos de Binance para el régimen"""
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

def check_recent_failure():
    """Revisa la base de datos de freqtrade. Si el último trade cerrado fue negativo, retorna True"""
    db_path = '/home/ubuntu/chacal/user_data/trifasico.sqlite'
    if not os.path.exists(db_path):
        return False
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('SELECT profit_ratio FROM trades WHERE is_open = 0 ORDER BY id DESC LIMIT 1')
        row = c.fetchone()
        conn.close()
        if row and row[0] is not None and row[0] < 0:
            return True
    except:
        pass
    return False

def main():
    token, chat_id = get_telegram_config()
    last_regime = None
    
    msg_init = "--- 🦅 CORE SNIPER RELOADED: CONFIGURACIÓN SIN BOZALES ACTIVADA ---"
    print(msg_init)
    send_telegram(token, chat_id, "🦅 [SISTEMA]: Cerebro Cuántico reiniciado. Bozales eliminados. Esperando entrada en mercado...")
    
    while True:
        df = get_btc_data()
        if df is not None:
            df['ema50'] = df['close'].ewm(span=EMA_PERIOD, adjust=False).mean()
            last_price = df['close'].iloc[-1]
            last_ema = df['ema50'].iloc[-1]
            diff_pct = (last_price / last_ema) - 1
            
            # 1. REFERENCIA BASE CLÁSICA (Régimen Trifásico FICT)
            if abs(diff_pct) <= LATERAL_ZONE:
                base_regime = "LATERAL_V4"
            elif diff_pct < TREND_THRESHOLD:
                base_regime = "ELITE_SNIPER_BEAR"  # Cubre el umbral hasta 4.3%
            else:
                base_regime = "ELITE_VOLUME_HUNTER" # Super-Bull
            
            # 2. SEGUERIDAD: EL PRECIO MANDA (Regla de Oro)
            # Eliminamos el intercalado por fallo para evitar bloqueos artificiales.
            regime = base_regime
            status_note = ""
            
            print(f"[{time.strftime('%H:%M:%S')}] BTC: ${last_price} | Diff: {round(diff_pct*100, 2)}% | Régimen: {regime}{status_note}", flush=True)

            if regime != last_regime:
                change_msg = f"🔄 CAMBIO DE RÉGIMEN: {last_regime} -> {regime}"
                print(change_msg, flush=True)
                send_telegram(token, chat_id, change_msg)

                if regime == "LATERAL_V4":
                    subprocess.run(["sudo", "systemctl", "stop", "ft-bear", "ft-bull"], check=False)
                    subprocess.run(["sudo", "systemctl", "start", "ft-lateral"], check=False)
                    send_telegram(token, chat_id, "🔮 MODO LATERAL V4 ACTIVADO (Termómetro 24/7)")
                elif regime == "ELITE_SNIPER_BEAR":
                    subprocess.run(["sudo", "systemctl", "stop", "ft-lateral", "ft-bull"], check=False)
                    subprocess.run(["sudo", "systemctl", "start", "ft-bear"], check=False)
                    send_telegram(token, chat_id, "🦅 SNIPER BEAR ACTIVADO (Especialista Bear/Lateral 7x)")
                else:
                    subprocess.run(["sudo", "systemctl", "stop", "ft-lateral", "ft-bear"], check=False)
                    subprocess.run(["sudo", "systemctl", "start", "ft-bull"], check=False)
                    send_telegram(token, chat_id, "🦊 VOLUME HUNTER ACTIVADO (Especialista Bull 10x)")
                
                last_regime = regime
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
