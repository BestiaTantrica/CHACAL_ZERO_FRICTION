# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
import numpy as np
import pandas as pd
from pandas import DataFrame
import talib.abstract as ta
from freqtrade.strategy import IStrategy, DecimalParameter, IntParameter

class ChacalLateralHunter_V1(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    use_custom_exit = True
    use_custom_stoploss = False
    
    # FORZAMOS ESTO PARA QUE NINGÚN CONFIG NOS ARRUINE
    trailing_stop = False 
    trailing_stop_positive = None
    trailing_stop_positive_offset = 0.0
    trailing_only_offset_is_reached = False

    # AJUSTE DE SENSIBILIDAD (Para bajar de 9000 trades a algo sano)
    # Proximidad: 0.001 significa que debe estar MUY pegado a la banda
    band_proximity = DecimalParameter(0.0005, 0.005, default=0.001, space='buy', optimize=True)
    lateral_threshold = DecimalParameter(0.015, 0.04, default=0.02, space='buy', optimize=True)
    bb_width_max = DecimalParameter(0.02, 0.08, default=0.04, space='buy', optimize=True)

    # PUNTERÍA 
    rsi_long_max  = IntParameter(20, 40, default=30, space='buy', optimize=True)
    rsi_short_min = IntParameter(60, 80, default=70, space='sell', optimize=True)

    stoploss = -0.04 # Stoploss duro al 4%
    timeframe = '5m'
    minimal_roi = {"0": 0.05} # Un profit mínimo del 5% como red de seguridad
    max_open_trades = 8

    def informative_pairs(self):
        return [('BTC/USDT:USDT', '1h')]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        bollinger = ta.BBANDS(dataframe, timeperiod=20, nbdevup=2.0, nbdevdn=2.0)
        dataframe['bb_upper'], dataframe['bb_mid'], dataframe['bb_lower'] = bollinger['upperband'], bollinger['middleband'], bollinger['lowerband']
        dataframe['bb_width'] = (dataframe['bb_upper'] - dataframe['bb_lower']) / dataframe['bb_mid']
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        
        # BTC 1h Macro
        btc_1h = self.dp.get_pair_dataframe(pair='BTC/USDT:USDT', timeframe='1h')
        if not btc_1h.empty:
            btc_1h['ema50'] = ta.EMA(btc_1h, timeperiod=50)
            dataframe = pd.merge(dataframe, btc_1h[['date', 'close', 'ema50']].rename(columns={'close': 'btc_close'}), on='date', how='left').ffill()
            dataframe['is_lateral'] = (dataframe['btc_close'] > dataframe['ema50']*(1-self.lateral_threshold.value)) & \
                                     (dataframe['btc_close'] < dataframe['ema50']*(1+self.lateral_threshold.value))
        else:
            dataframe['is_lateral'] = False
            
        # Puntos de calidad: Está lateral y el ancho de BB es razonable
        dataframe['score'] = (dataframe['is_lateral'] == True).astype(int) + (dataframe['bb_width'] < self.bb_width_max.value).astype(int)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Long: Score perfecto + toca banda baja + RSI bajo
        long_cond = (dataframe['score'] == 2) & \
                    (dataframe['close'] <= dataframe['bb_lower'] * (1 + self.band_proximity.value)) & \
                    (dataframe['rsi'] < self.rsi_long_max.value)
        
        # Short: Score perfecto + toca banda alta + RSI alto
        short_cond = (dataframe['score'] == 2) & \
                     (dataframe['close'] >= dataframe['bb_upper'] * (1 - self.band_proximity.value)) & \
                     (dataframe['rsi'] > self.rsi_short_min.value)

        dataframe.loc[long_cond, ['enter_long', 'enter_tag']] = [1, 'LAT_LONG']
        dataframe.loc[short_cond, ['enter_short', 'enter_tag']] = [1, 'LAT_SHORT']
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Requisito de la interfaz Freqtrade (salimos vía custom_exit)
        return dataframe

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if len(dataframe) == 0: return None
        
        last = dataframe.iloc[-1]
        
        # Salida al centro del canal (Media de Bollinger) solo si estamos en positivo
        if trade.is_short and last['close'] <= last['bb_mid'] and current_profit > 0: return 'TARGET_MID'
        if not trade.is_short and last['close'] >= last['bb_mid'] and current_profit > 0: return 'TARGET_MID'
        
        # Breakout de emergencia (ya no es lateral)
        if not last['is_lateral']: return 'MACRO_BREAKOUT'
        
        return None
