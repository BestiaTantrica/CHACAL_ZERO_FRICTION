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

class ChacalLateralFinal_V1(IStrategy):
    """
    ESTRATEGIA CHACAL LATERAL - VERSIÓN FINAL BLINDADA
    DNA ÉPOCA 62 + MIRA 1M + GESTIÓN 6H
    """
    INTERFACE_VERSION = 3
    can_short = True
    use_custom_exit = True
    use_custom_stoploss = True
    
    # --- BLOQUEO TOTAL DE TRAILING STOP ---
    trailing_stop = False 
    trailing_stop_positive = None
    trailing_stop_positive_offset = 0.0
    trailing_only_offset_is_reached = False

    # --- PARÁMETROS ÉPOCA 62 (DNA REAL) ---
    band_proximity    = DecimalParameter(0.0005, 0.005, default=0.002, space='buy', optimize=True)
    lateral_threshold = DecimalParameter(0.015, 0.05, default=0.039, space='buy', optimize=True)
    bb_width_max      = DecimalParameter(0.02, 0.15, default=0.08, space='buy', optimize=True)
    bb_width_min      = DecimalParameter(0.001, 0.02, default=0.005, space='buy', optimize=True)
    adx_limit         = IntParameter(15, 40, default=21, space='buy', optimize=True)
    rsi_long_max      = IntParameter(20, 40, default=30, space='buy', optimize=True)
    rsi_short_min     = IntParameter(40, 80, default=70, space='sell', optimize=True)

    # --- MIRA 1m (PRECISIÓN INSTITUCIONAL) ---
    rsi_1m_long       = IntParameter(15, 45, default=25, space='buy', optimize=True)
    rsi_1m_short      = IntParameter(55, 85, default=75, space='sell', optimize=True)

    stoploss = -0.05 
    timeframe = '5m'
    minimal_roi = {"0": 100} 
    max_open_trades = 8

    def informative_pairs(self):
        pairs = self.dp.current_whitelist()
        informative = [('BTC/USDT:USDT', '1h')]
        for pair in pairs:
            informative.append((pair, '1m'))
        return informative

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        bollinger = ta.BBANDS(dataframe, timeperiod=20, nbdevup=2.0, nbdevdn=2.0)
        dataframe['bb_upper'], dataframe['bb_mid'], dataframe['bb_lower'] = bollinger['upperband'], bollinger['middleband'], bollinger['lowerband']
        dataframe['bb_width'] = (dataframe['bb_upper'] - dataframe['bb_lower']) / dataframe['bb_mid']
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['adx'] = ta.ADX(dataframe, timeperiod=14)
        
        # Macro BTC 1h
        btc_1h = self.dp.get_pair_dataframe(pair='BTC/USDT:USDT', timeframe='1h')
        if not btc_1h.empty:
            btc_1h['ema50'] = ta.EMA(btc_1h, timeperiod=50)
            dataframe = pd.merge(dataframe, btc_1h[['date', 'close', 'ema50']].rename(columns={'close': 'btc_close'}), on='date', how='left').ffill()
            dataframe['is_lateral'] = (dataframe['btc_close'] > dataframe['ema50']*(1-self.lateral_threshold.value)) & \
                                     (dataframe['btc_close'] < dataframe['ema50']*(1+self.lateral_threshold.value))
        else:
            dataframe['is_lateral'] = False
            
        dataframe['prep_ready'] = (
            (dataframe['is_lateral'] == True) & 
            (dataframe['bb_width'] < self.bb_width_max.value) & 
            (dataframe['bb_width'] > self.bb_width_min.value) & 
            (dataframe['adx'] > self.adx_limit.value)
        ).astype(int)

        inf_1m = self.dp.get_pair_dataframe(pair=metadata['pair'], timeframe='1m')
        if not inf_1m.empty:
            inf_1m['rsi_1m'] = ta.RSI(inf_1m, timeperiod=14)
            dataframe = pd.merge(dataframe, inf_1m[['date', 'rsi_1m']], on='date', how='left').ffill()
        else:
            dataframe['rsi_1m'] = 50

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        long_cond = (
            (dataframe['prep_ready'] == 1) & 
            (dataframe['close'] <= dataframe['bb_lower'] * (1 + self.band_proximity.value)) & 
            (dataframe['rsi'] < self.rsi_long_max.value) & 
            (dataframe['rsi_1m'] < self.rsi_1m_long.value)
        )
        
        short_cond = (
            (dataframe['prep_ready'] == 1) & 
            (dataframe['close'] >= dataframe['bb_upper'] * (1 - self.band_proximity.value)) & 
            (dataframe['rsi'] > self.rsi_short_min.value) & 
            (dataframe['rsi_1m'] > self.rsi_1m_short.value)
        )

        dataframe.loc[long_cond, ['enter_long', 'enter_tag']] = [1, 'LAT_LONG_FINE']
        dataframe.loc[short_cond, ['enter_short', 'enter_tag']] = [1, 'LAT_SHORT_FINE']
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if len(dataframe) == 0: return None
        last = dataframe.iloc[-1]
        
        trade_duration = (current_time - trade.open_date_utc).total_seconds() / 3600
        if trade_duration > 6.0: return 'TIME_EXIT_6H'
        
        if trade.is_short and last['close'] <= last['bb_mid'] and current_profit > 0: return 'TARGET_MID'
        if not trade.is_short and last['close'] >= last['bb_mid'] and current_profit > 0: return 'TARGET_MID'
        
        if not last['is_lateral']: return 'MACRO_BREAKOUT'
        
        return None

    def custom_stoploss(self, pair: str, trade: Trade, current_time: datetime,
                        current_rate: float, current_profit: float, **kwargs) -> float:
        return self.stoploss

    def leverage(self, *args, **kwargs) -> float:
        return 5.0
