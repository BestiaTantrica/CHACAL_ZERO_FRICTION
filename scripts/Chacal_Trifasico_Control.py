import pandas as pd
import numpy as np
import time
import os
import subprocess
import requests

# CONFIGURACIÓN ELITE V4.0 (The Sniper King)
LATERAL_THRESHOLD = 0.043
EMA_PERIOD = 50
TIMEFRAME = '1h'
BTC_SYMB = 'BTC/USDT:USDT'

# CONFIGURACIÓN TELEGRAM (Sincronizada con el bot)
# Estos campos se llenarán con los datos de tu config.json en AWS
TELEGRAM_TOKEN = "" # Se rellena en AWS
TELEGRAM_CHAT_ID = "" 

class ChacalTrifasicoControl:
    def __init__(self, btc_data_path):
        self.btc_data_path = btc_data_path
        self.current_regime = None

    def calculate_regime(self, df):
        """
        Determina el régimen de mercado basado en BTC/USDT 1h
        """
        if df.empty:
            return "UNKNOWN"

        # Calcular EMA50
        df['ema50'] = df['close'].ewm(span=EMA_PERIOD, adjust=False).mean()
        
        last_price = df['close'].iloc[-1]
        last_ema = df['ema50'].iloc[-1]
        
        # Lógica Lateral (Umbral porcentual sobre EMA50)
        upper_limit = last_ema * (1 + LATERAL_THRESHOLD)
        lower_limit = last_ema * (1 - LATERAL_THRESHOLD)
        
        is_lateral = (last_price > lower_limit) and (last_price < upper_limit)
        
        if is_lateral:
            return "MODO_LATERAL" # Especialista: Lateral Hunter V4
        elif last_price > last_ema:
            return "MODO_BULL"    # Especialista: Volume Hunter
        else:
            return "MODO_BEAR"    # Especialista: Sniper Bear
            
    def get_status_report(self, df):
        regime = self.calculate_regime(df)
        last_price = df['close'].iloc[-1]
        last_ema = df['ema50'].iloc[-1]
        diff_pct = ((last_price / last_ema) - 1) * 100
        
        report = {
            "regime": regime,
            "btc_price": round(last_price, 2),
            "btc_ema50": round(last_ema, 2),
            "diff_ema_pct": round(diff_pct, 2),
            "specialist": self.get_active_specialist(regime)
        }
        return report

    def send_telegram(self, message):
        """Envía notificaciones al Telegram del Capitán"""
        if not TELEGRAM_TOKEN: return
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": f"🦅 [CEREBRO CHACAL]: {message}"}
        try:
            requests.post(url, json=payload, timeout=10)
        except:
            pass

    def switch_regime(self, new_regime):
        """
        Ejecuta la conmutación activa de servicios systemd para evitar colisiones
        """
        if new_regime == self.current_regime:
            return

        msg = f"🔄 CAMBIO DE RÉGIMEN: {self.current_regime} -> {new_regime}"
        print(msg)
        self.send_telegram(msg)
        
        if new_regime in ["MODO_LATERAL", "MODO_BEAR"]:
            subprocess.run(["sudo", "systemctl", "stop", "ft-bull"], check=False)
            subprocess.run(["sudo", "systemctl", "start", "ft-bear"], check=False)
            self.send_telegram("🦅 SNIPER BEAR ACTIVADO (7x)")
        
        elif new_regime == "MODO_BULL":
            subprocess.run(["sudo", "systemctl", "stop", "ft-bear"], check=False)
            subprocess.run(["sudo", "systemctl", "start", "ft-bull"], check=False)
            self.send_telegram("🦊 VOLUME HUNTER ACTIVADO (10x Sniper)")
            
        self.current_regime = new_regime

    def get_active_specialist(self, regime):
        if regime in ["MODO_LATERAL", "MODO_BEAR"]:
            return "🦅 Sniper Bear ULTRA (7x)"
        elif regime == "MODO_BULL":
            return "🦊 Volume Hunter (10x Sniper)"
        return "NUNCA_OPERAR"

if __name__ == "__main__":
    print("--- CHACAL ZERO FRICTION: CONTROL ELITE V4.0 ---")
    
    # En producción este script corre dentro de la carpeta /home/ubuntu/chacal
    # Intentamos leer el config para Telegram si existe
    try:
        import json
        with open('/home/ubuntu/freqtrade/user_data/configs/config.json') as f:
            cfg = json.load(f)
            TELEGRAM_TOKEN = cfg['telegram']['token']
            TELEGRAM_CHAT_ID = cfg['telegram']['chat_id']
    except:
        pass

    control = ChacalTrifasicoControl(None)
    
    while True:
        try:
            # En producción esto lee de la DB o API de Binance
            # Usaremos el comando freqtrade list-data o similar para obtener precio fresco
            # Simplificamos: el orquestador lee los últimos logs o usa ccxt
            import ccxt
            exchange = ccxt.binance()
            ohlcv = exchange.fetch_ohlcv('BTC/USDT', timeframe='1h', limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            status = control.get_status_report(df)
            print(f"[{time.ctime()}] Regime: {status['regime']} | BTC: {status['btc_price']}")
            
            control.switch_regime(status['regime'])
        except Exception as e:
            print(f"Error en bucle: {e}")
            
        time.sleep(60)
