import pandas as pd
import numpy as np
from freqtrade.strategy import IStrategy, DecimalParameter, IntParameter
from pandas import DataFrame
import talib.abstract as ta

class ChacalArena_FanHunter(IStrategy):
    """
    CHACAL ARENA - FAN HUNTER (V5.0 - SHORT ONLY)
    Tríada de la Arena: OG, SANTOS, LAZIO
    Especialista en reversión de eventos pre-calendario.
    
    CALENDARIO OPERATIVO PRINCIPAL:
    - Viernes, Sábados, Domingos (Fines de semana de ligas/torneos).
    """
    INTERFACE_VERSION = 3
    timeframe = '1m'
    
    # --- Parámetros del Fino ---
    # Ignición (Long)
    z_threshold_long = DecimalParameter(6.0, 15.0, default=10.0, space='buy')
    rsi_max_long = IntParameter(50, 75, default=65, space='buy') # Solo si no está ya volando
    
    # Agotamiento (Short)
    rsi_min_short = IntParameter(80, 95, default=88, space='sell')
    
    # Gestión de Riesgo
    minimal_roi = {
        "0": 0.08,  # Target 8% rápido
        "15": 0.04, # Bajar a 4% si se estanca
        "30": 0.02
    }
    
    stoploss = -0.04 # 4% de SL para aguantar mechas
    trailing_stop = True
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.02
    
    process_only_new_candles = True
    use_exit_signal = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # 1. Z-Score (Detección de anomalía de volumen)
        dataframe['vol_mean'] = dataframe['volume'].rolling(window=1440).mean()
        dataframe['vol_std'] = dataframe['volume'].rolling(window=1440).std()
        dataframe['z_score'] = (dataframe['volume'] - dataframe['vol_mean']) / dataframe['vol_std']
        
        # 2. RSI (Detección de sobrecompra/venta)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        
        # 3. FILTRO DE MAGNITUD (La clave para absorber comisiones)
        # Calcula si el precio ha subido al menos un X% desde el mínimo de la última hora
        dataframe['min_60'] = dataframe['low'].rolling(window=60).min()
        dataframe['pump_60m'] = (dataframe['close'] - dataframe['min_60']) / dataframe['min_60'] * 100
        
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # --- MODO SHORT ONLY (La Triada de la Arena rinde mejor a la contra) ---
        dataframe.loc[
            (
                (dataframe['rsi'] > self.rsi_min_short.value) & # Agotamiento masivo
                (dataframe['pump_60m'] > 3.0) # Confirmación real del evento de anticipación
            ),
            'enter_short'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Salida por agotamiento de tendencia si no tocó ROI
        dataframe.loc[
            (
                (dataframe['rsi'] > 85) # Salida LONG por seguridad extrema
            ),
            'exit_long'] = 1
            
        dataframe.loc[
            (
                (dataframe['rsi'] < 45) # Salida SHORT (Reversión completada)
            ),
            'exit_short'] = 1

        return dataframe
