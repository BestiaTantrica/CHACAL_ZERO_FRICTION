# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
import numpy as np
import pandas as pd
from pandas import DataFrame
from datetime import datetime
import talib.abstract as ta
from freqtrade.strategy import IStrategy, DecimalParameter, IntParameter
from freqtrade.persistence import Trade

class ChacalMicro_V1(IStrategy):
    """
    CHACAL MICRO V1 - ESTUDIO DE PATRONES EN 1M
    Versión adaptada de la V4 para backtesting en datasets 'Frankenstein' (solo lateral).
    Elimina filtros macro para enfocarse puramente en la micro-estructura de 1m.
    """
    INTERFACE_VERSION = 3
    can_short = True
    use_custom_exit = True
    use_custom_stoploss = False
    
    # --- BLOQUEO TOTAL DE TRAILING STOP ---
    trailing_stop = False 
    trailing_stop_positive = None
    trailing_stop_positive_offset = 0.0
    trailing_only_offset_is_reached = False

    # --- DNA MICRO (1m) ---
    band_proximity    = DecimalParameter(0.0001, 0.002, default=0.0005, space='buy', optimize=True)
    bb_width_max      = DecimalParameter(0.005, 0.05, default=0.015, space='buy', optimize=True)
    bb_width_min      = DecimalParameter(0.0001, 0.005, default=0.001, space='buy', optimize=True)
    adx_limit         = IntParameter(10, 30, default=15, space='buy', optimize=True)

    # --- GATILLOS DE SCORING ---
    score_threshold_long  = IntParameter(1, 4, default=2, space='buy', optimize=True)
    score_threshold_short = IntParameter(1, 4, default=2, space='sell', optimize=True)
    
    # --- FILTROS RSI ---
    rsi_long_max      = IntParameter(20, 45, default=35, space='buy', optimize=True)
    rsi_short_min     = IntParameter(55, 80, default=65, space='sell', optimize=True)

    stoploss = -0.03 
    timeframe = '1m'
    minimal_roi = {"0": 100} 
    max_open_trades = 10

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # 1. BBANDS (1m)
        bollinger = ta.BBANDS(dataframe, timeperiod=20, nbdevup=2.0, nbdevdn=2.0)
        dataframe['bb_upper'], dataframe['bb_mid'], dataframe['bb_lower'] = bollinger['upperband'], bollinger['middleband'], bollinger['lowerband']
        dataframe['bb_width'] = (dataframe['bb_upper'] - dataframe['bb_lower']) / dataframe['bb_mid']
        
        # 2. RSI y ADX (1m)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['adx'] = ta.ADX(dataframe, timeperiod=14)
        dataframe['ema_slow'] = ta.EMA(dataframe, timeperiod=50)
        dataframe['vol_mean'] = dataframe['volume'].rolling(10).mean()
        
        # --- COMPONENTES DEL SCORING (Directo en 1m) ---
        # 1. Price Action Confirmation
        dataframe['pa_bullish'] = (dataframe['close'] > dataframe['open']).astype(int)
        dataframe['pa_bearish'] = (dataframe['close'] < dataframe['open']).astype(int)
        
        # 2. Agotamiento
        dataframe['exhaust_long'] = (dataframe['rsi'] < 30).astype(int)
        dataframe['exhaust_short'] = (dataframe['rsi'] > 70).astype(int)
        
        # 3. Divergencia Simple
        dataframe['div_bullish'] = ((dataframe['close'] <= dataframe['close'].shift(1)) & (dataframe['rsi'] > dataframe['rsi'].shift(1))).astype(int)
        dataframe['div_bearish'] = ((dataframe['close'] >= dataframe['close'].shift(1)) & (dataframe['rsi'] < dataframe['rsi'].shift(1))).astype(int)
        
        # 4. Airbag Persistencia (3 velas por debajo de EMA con volumen)
        dataframe['airbag_long_trigger'] = ((dataframe['close'] < dataframe['ema_slow']) & (dataframe['volume'] > dataframe['vol_mean'])).rolling(3).min()
        dataframe['airbag_short_trigger'] = ((dataframe['close'] > dataframe['ema_slow']) & (dataframe['volume'] > dataframe['vol_mean'])).rolling(3).min()
        
        # Construcción del SCORING
        dataframe['score_long'] = dataframe['pa_bullish'] + dataframe['exhaust_long'] + dataframe['div_bullish']
        dataframe['score_short'] = dataframe['pa_bearish'] + dataframe['exhaust_short'] + dataframe['div_bearish']

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        long_cond = (
            (dataframe['bb_width'] < self.bb_width_max.value) & 
            (dataframe['bb_width'] > self.bb_width_min.value) & 
            (dataframe['adx'] > self.adx_limit.value) &
            (dataframe['close'] <= dataframe['bb_lower'] * (1 + self.band_proximity.value)) & 
            (dataframe['rsi'] < self.rsi_long_max.value) &
            (dataframe['score_long'] >= self.score_threshold_long.value)
        )
        
        short_cond = (
            (dataframe['bb_width'] < self.bb_width_max.value) & 
            (dataframe['bb_width'] > self.bb_width_min.value) & 
            (dataframe['adx'] > self.adx_limit.value) &
            (dataframe['close'] >= dataframe['bb_upper'] * (1 - self.band_proximity.value)) & 
            (dataframe['rsi'] > self.rsi_short_min.value) &
            (dataframe['score_short'] >= self.score_threshold_short.value)
        )

        dataframe.loc[long_cond, ['enter_long', 'enter_tag']] = [1, 'MICRO_LONG']
        dataframe.loc[short_cond, ['enter_short', 'enter_tag']] = [1, 'MICRO_SHORT']
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if len(dataframe) == 0: return None
        last = dataframe.iloc[-1]
        
        # 1. ANTI-ZOMBIES
        trade_duration = (current_time - trade.open_date_utc).total_seconds() / 3600
        if trade_duration > 4.0: return 'TIME_EXIT_4H'
        
        # 2. SALIDA NÚCLEO (TARGET_MID)
        if trade.is_short and last['close'] <= last['bb_mid'] and current_profit > 0: return 'TARGET_MID'
        if not trade.is_short and last['close'] >= last['bb_mid'] and current_profit > 0: return 'TARGET_MID'
        
        # 3. SALIDA AIRBAG
        if current_profit < -0.015:
            if not trade.is_short:
                if last.get('airbag_long_trigger', 0) == 1: return 'AIRBAG_DUMP'
            else:
                if last.get('airbag_short_trigger', 0) == 1: return 'AIRBAG_PUMP'
        
        return None

    def leverage(self, *args, **kwargs) -> float:
        return 7.0
