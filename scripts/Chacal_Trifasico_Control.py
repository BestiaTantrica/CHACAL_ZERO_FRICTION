import pandas as pd
import numpy as np
import time
import os

# CONFIGURACIÓN TRIFÁSICA (Sincronizada con DNA 62 y Sniper ULTRA)
LATERAL_THRESHOLD = 0.039  # 3.9% de desviación de EMA50
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

    def get_active_specialist(self, regime):
        mapping = {
            "MODO_LATERAL": "🔮 Lateral Hunter V4",
            "MODO_BULL": "🦊 Volume Hunter",
            "MODO_BEAR": "🦅 Sniper Bear ULTRA"
        }
        return mapping.get(regime, "NUNCA_OPERAR")

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
