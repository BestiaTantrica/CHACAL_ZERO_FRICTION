import pandas as pd
import numpy as np
import time
import os
import subprocess

# CONFIGURACIÓN ELITE V4.0 (The Sniper King)
LATERAL_THRESHOLD = 0.043  # 4.3% de desviación de EMA50
EMA_PERIOD = 50
TIMEFRAME = '1h'

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

    def switch_regime(self, new_regime):
        """
        Ejecuta la conmutación activa de servicios systemd para evitar colisiones
        """
        if new_regime == self.current_regime:
            return

        print(f"🔄 CAMBIO DE RÉGIMEN DETECTADO: {self.current_regime} -> {new_regime}")
        
        # Mapeo de regímenes a servicios
        # Sniper Bear domina Lateral y Bear
        if new_regime in ["MODO_LATERAL", "MODO_BEAR"]:
            print("🚀 Activando Especialista Francotirador: SNIPER BEAR")
            subprocess.run(["sudo", "systemctl", "stop", "ft-bull"], check=False)
            subprocess.run(["sudo", "systemctl", "start", "ft-bear"], check=False)
        
        elif new_regime == "MODO_BULL":
            print("🚀 Activando Especialista de Euforia: VOLUME HUNTER")
            subprocess.run(["sudo", "systemctl", "stop", "ft-bear"], check=False)
            subprocess.run(["sudo", "systemctl", "start", "ft-bull"], check=False)
            
        self.current_regime = new_regime

    def get_active_specialist(self, regime):
        if regime in ["MODO_LATERAL", "MODO_BEAR"]:
            return "🦅 Sniper Bear ULTRA (7x)"
        elif regime == "MODO_BULL":
            return "🦊 Volume Hunter (10x Sniper)"
        return "NUNCA_OPERAR"

if __name__ == "__main__":
    print("--- CHACAL ZERO FRICTION: CONTROL TRIFÁSICO ---")
    # Mock para demostración del concepto
    # En producción: esto leería de la API de Binance o del archivo de datos de Freqtrade
    data = {
        'close': [62000, 61500, 61000, 60500, 59000, 58000, 57000, 56000] # Ejemplo dump Junio
    }
    df_example = pd.DataFrame(data)
    
    control = ChacalTrifasicoControl(None)
    status = control.get_status_report(df_example)
    
    print(f"Régimen Detectado: {status['regime']}")
    print(f"Especialista Activo: {status['specialist']}")
    print(f"Desviación EMA50: {status['diff_ema_pct']}%")
