import pandas as pd
import numpy as np
from freqtrade.strategy import IStrategy, DecimalParameter, IntParameter
from pandas import DataFrame
import talib.abstract as ta

class ChacalArena_FanHunter(IStrategy):
    """
    CHACAL ARENA - FAN HUNTER (V1.0)
    Especialista en Eventos y Pumps Volátiles (Fan Tokens)
    Estrategia Dual: Caza de Ignición y Short de Agotamiento.
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
        # 1. Z-Score de Volumen (La clave de la ignición)
        dataframe['vol_mean'] = dataframe['volume'].rolling(window=1440).mean()
        dataframe['vol_std'] = dataframe['volume'].rolling(window=1440).std()
        dataframe['z_score'] = (dataframe['volume'] - dataframe['vol_mean']) / dataframe['vol_std']
        
        # 2. RSI (Detección de sobrecompra/venta)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        
        # 3. EMA20 (Filtro de tendencia micro)
        dataframe['ema20'] = ta.EMA(dataframe, timeperiod=20)
        
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # --- Lógica LONG (Ignition) ---
        # Solo permitimos LONG en SANTOS según backtest de ruido
        if metadata['pair'] == 'SANTOS/USDT':
            dataframe.loc[
                (
                    (dataframe['z_score'] > self.z_threshold_long.value) &
                    (dataframe['rsi'] < self.rsi_max_long.value) &
                    (dataframe['close'] > dataframe['ema20'])
                ),
                'enter_long'] = 1

        # --- Lógica SHORT (Exhaustion) ---
        # SHORT permitido en todos (Es nuestra mayor fuente de profit)
        dataframe.loc[
            (
                (dataframe['rsi'] > self.rsi_min_short.value)
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
