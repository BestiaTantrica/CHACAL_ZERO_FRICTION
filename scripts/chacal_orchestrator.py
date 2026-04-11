import subprocess
import time
import pandas as pd
import numpy as np
import requests
import os
import json

# ================================================================
# 🦅 CHACAL ORCHESTRATOR V4.0 - THE SNIPER KING EDITION
# ================================================================

LATERAL_THRESHOLD = 0.043  # 4.3% (Optimizado para +527% ROI)
EMA_PERIOD = 50
CHECK_INTERVAL = 60        # Chequeo cada minuto

def get_telegram_config():
    """Busca el token y chat_id en el config.json de Freqtrade"""
    try:
        with open('/home/ubuntu/freqtrade/user_data/configs/config.json') as f:
            cfg = json.load(f)
            return cfg['telegram']['token'], cfg['telegram']['chat_id']
    except Exception as e:
        print(f"Error cargando Telegram Config: {e}")
        return None, None

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

def main():
    token, chat_id = get_telegram_config()
    last_regime = None
    
    msg_init = "--- INICIANDO CEREBRO SNIPER KING V4.0 (+527% ROI) ---"
    print(msg_init)
    # No enviamos el init para no spamear si hay reinicios por error
    
    while True:
        df = get_btc_data()
        if df is not None:
            df['ema50'] = df['close'].ewm(span=EMA_PERIOD, adjust=False).mean()
            last_price = df['close'].iloc[-1]
            last_ema = df['ema50'].iloc[-1]
            diff_pct = (last_price / last_ema) - 1
            
            # --- LÓGICA DUAL ELITE ---
            # Si BTC < EMA50 + 4.3% -> Sniper Bear domina (Lateral y Bear)
            # Si BTC > EMA50 + 4.3% -> Volume Hunter domina (Fomo/Pure Bull)
            
            if diff_pct < LATERAL_THRESHOLD:
                regime = "ELITE_SNIPER_BEAR" # Cubre Lateral y Bear
            else:
                regime = "ELITE_VOLUME_HUNTER" # Cubre Bull Extremo
            
            print(f"[{time.strftime('%H:%M:%S')}] BTC: ${last_price} | Diff: {round(diff_pct*100, 2)}% | Régimen: {regime}", flush=True)

            if regime != last_regime:
                change_msg = f"🔄 CAMBIO DE RÉGIMEN: {last_regime} -> {regime}"
                print(change_msg, flush=True)
                send_telegram(token, chat_id, change_msg)

                if regime == "ELITE_SNIPER_BEAR":
                    subprocess.run(["sudo", "systemctl", "stop", "ft-bull"], check=False)
                    subprocess.run(["sudo", "systemctl", "start", "ft-bear"], check=False)
                    send_telegram(token, chat_id, "🦅 SNIPER BEAR ACTIVADO (Especialista 7x)")
                else:
                    subprocess.run(["sudo", "systemctl", "stop", "ft-bear"], check=False)
                    subprocess.run(["sudo", "systemctl", "start", "ft-bull"], check=False)
                    send_telegram(token, chat_id, "🦊 VOLUME HUNTER ACTIVADO (Especialista 10x)")
                
                last_regime = regime
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
