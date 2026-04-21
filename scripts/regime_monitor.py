import requests
import pandas as pd
import time
from datetime import datetime
import talib.abstract as ta

# Configuración
TELEGRAM_TOKEN = "7998240806:AAECN0ypjqOwFDR6c1SOn6rW2Hlb3OD7wNA" # Desde el config.json
CHAT_ID = "6527908321"

def send_telegram_msg(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error enviando telegram: {e}")

def get_btc_data():
    # Obtiene datos de klines de Binance (1h)
    url = "https://fapi.binance.com/fapi/v1/klines"
    params = {
        "symbol": "BTCUSDT",
        "interval": "1h",
        "limit": 60 # Necesitamos al menos 50 para la EMA50
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'])
        df['close'] = df['close'].astype(float)
        return df
    except Exception as e:
        print(f"Error obteniendo datos de Binance: {e}")
        return None

def check_regime():
    df = get_btc_data()
    if df is None or len(df) < 50:
        return None, None, None
        
    df['ema50'] = ta.EMA(df, timeperiod=50)
    
    last_candle = df.iloc[-1]
    current_price = last_candle['close']
    ema50 = last_candle['ema50']
    
    if pd.isna(ema50):
        return None, None, None
        
    diff_pct = ((current_price - ema50) / ema50) * 100
    
    if current_price < ema50:
        regime = "BEAR"
    else:
        regime = "BULL"
        
    return regime, current_price, ema50, diff_pct

def main():
    print("Iniciando Monitor de Regimen Chacal...")
    last_alerted_regime = None
    consecutive_hours = 0
    
    while True:
        try:
            regime, price, ema50, diff_pct = check_regime()
            
            if regime:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] BTC: ${price:.2f} | EMA50: ${ema50:.2f} | Diff: {diff_pct:+.2f}% | Regime: {regime}")
                
                # Check consecutive regime to avoid noise
                if regime != last_alerted_regime:
                    consecutive_hours += 1
                    # Alerta si el regimen se mantiene por 3 horas consecutivas
                    if consecutive_hours >= 3:
                        if regime == "BEAR":
                            msg = f"🐻 *ALERTA: RÉGIMEN CAMBIA A BEAR*\n\nBTC rompió EMA50 hacia abajo y se mantuvo.\n\nBTC Actual: ${price:,.2f}\nEMA50: ${ema50:,.2f} ({diff_pct:+.2f}% debajo)\n\n*ACCIÓN SUGERIDA:*\n→ Detener BULL\n→ Activar BEAR\n`cd MIGRACION_BEAR_AWS`"
                        else:
                            msg = f"🦊 *ALERTA: RÉGIMEN CAMBIA A BULL*\n\nBTC superó EMA50 hacia arriba y se mantuvo.\n\nBTC Actual: ${price:,.2f}\nEMA50: ${ema50:,.2f} ({diff_pct:+.2f}% encima)\n\n*ACCIÓN SUGERIDA:*\n→ Detener BEAR\n→ Activar BULL\n`cd MIGRACION_BULL_AWS`"
                            
                        send_telegram_msg(msg)
                        last_alerted_regime = regime
                        consecutive_hours = 0
                        print(f"Alerta enviada: Cambio a {regime}")
                else:
                    consecutive_hours = 0
            
            # Dormir 1 hora
            time.sleep(3600)
            
        except Exception as e:
            print(f"Error en loop principal: {e}")
            time.sleep(300) # Reintentar en 5 min si hay error

if __name__ == "__main__":
    main()
