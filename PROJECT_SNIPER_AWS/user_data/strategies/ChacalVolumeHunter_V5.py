# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
"""
CHACAL VOLUME HUNTER V5 — ELITE DUAL BULL
=========================================
- Mejoras:
    1. Fuzzy confidence logic para is_bull_market.
    2. Reducción de ventanas rolling para ahorro de RAM.
    3. Leverage dinámico ATR-based.
    4. Guardias de tiempo optimizadas.
"""
import numpy as np
import pandas as pd
from pandas import DataFrame
from datetime import datetime
from typing import Optional, Any, Dict
import talib.abstract as ta
from freqtrade.strategy import IStrategy, DecimalParameter, IntParameter
from freqtrade.persistence import Trade

class ChacalVolumeHunter_V5(IStrategy):
    INTERFACE_VERSION = 3
    can_short = False
    use_custom_exit = True
    use_custom_stoploss = True
    
    trailing_stop = True
    trailing_stop_positive = 0.005
    trailing_stop_positive_offset = 0.025
    trailing_only_offset_is_reached = True
    
    position_adjustment_enable = True
    stoploss_atr_mult = DecimalParameter(1.2, 2.5, default=1.8, space='sell', load=True)
    rsi_buy_min = IntParameter(15, 35, default=21, space='buy', load=True)
    btc_threshold_mult = DecimalParameter(1.0, 2.5, default=1.2, space='buy', load=True)

    dca_enabled = True
    max_dca_orders = 2
    w_corr = DecimalParameter(0.30, 0.60, default=0.45, space='buy', load=True)
    w_atr = DecimalParameter(0.10, 0.40, default=0.20, space='buy', load=True)
    
    # Reducción de ventana rolling para optimizar RAM (144 -> 72)
    corr_window = 72 
    
    stoploss = -0.99 
    timeframe = '5m'
    inf_timeframe = '1h'
    max_open_trades = 8
    startup_candle_count: int = 200

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # BASE
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=14)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['volume_mean'] = dataframe['volume'].rolling(30).mean()
        
        # BTC DATA
        btc_5m = self.dp.get_pair_dataframe(pair="BTC/USDT:USDT", timeframe=self.timeframe).copy()
        btc_1h = self.dp.get_pair_dataframe(pair="BTC/USDT:USDT", timeframe=self.inf_timeframe).copy()
        
        if not btc_5m.empty:
            btc_5m['btc_5m_rsi'] = ta.RSI(btc_5m, timeperiod=14)
            btc_5m['btc_5m_std'] = btc_5m['close'].pct_change().rolling(24).std()
            btc_5m['btc_5m_close'] = btc_5m['close']
            dataframe = pd.merge(dataframe, btc_5m[['date', 'btc_5m_rsi', 'btc_5m_std', 'btc_5m_close']], on='date', how='left')
            
        if not btc_1h.empty:
            btc_1h['btc_rsi_1h'] = ta.RSI(btc_1h, timeperiod=14)
            btc_1h['btc_atr'] = ta.ATR(btc_1h, timeperiod=14)
            btc_1h.set_index('date', inplace=True)
            aligned = btc_1h[['btc_rsi_1h', 'btc_atr']].reindex(dataframe['date']).ffill()
            dataframe['btc_rsi_1h'] = aligned['btc_rsi_1h'].values
            dataframe['btc_atr'] = aligned['btc_atr'].values

        # FUZZY BULL CONFIDENCE
        # (rsi_1h - 40) / 30 -> 0 a 1 si el RSI está entre 40 y 70
        # (rsi_5m - 45) / 30 -> 0 a 1 si el RSI 5m está entre 45 y 75
        dataframe['bull_confidence'] = (
            0.5 * (dataframe['btc_rsi_1h'] - 40).clip(0, 30) / 30 +
            0.5 * (dataframe['btc_5m_rsi'] - 45).clip(0, 30) / 30
        )
        dataframe['is_bull_market'] = (dataframe['bull_confidence'] > 0.4)

        # ATRASO REAL Y CORRELACIÓN (Ventana reducida)
        dataframe['atraso_real'] = dataframe['btc_5m_close'].pct_change(5) - dataframe['close'].pct_change(5)
        dataframe['corr_btc'] = dataframe['close'].pct_change().rolling(self.corr_window).corr(dataframe['btc_5m_close'].pct_change()).fillna(0.8)

        # RISK PRESSURE
        atr_pct = dataframe['atr'] / dataframe['close']
        dataframe['risk_pressure_score'] = (
            float(self.w_corr.value) * (1 - dataframe['corr_btc']) + 
            float(self.w_atr.value) * atr_pct.rolling(self.corr_window).rank(pct=True).fillna(0.5)
        ).clip(0, 1)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dynamic_threshold = dataframe['btc_5m_std'] * float(self.btc_threshold_mult.value)
        time_guard = (dataframe['date'].dt.hour >= 6) & (dataframe['date'].dt.hour < 21)

        # Lógica BULL ATRASO V5 (Usando confidence)
        bull_long = (
            dataframe['is_bull_market'] &
            time_guard &
            (dataframe['atraso_real'] > dynamic_threshold) &
            (dataframe['volume'] > (dataframe['volume_mean'] * 1.3)) &
            (dataframe['risk_pressure_score'] < 0.45)
        )

        # Lógica LATERAL RSI
        lateral_long = (
            (dataframe['bull_confidence'] > 0.3) &
            time_guard &
            (dataframe['btc_5m_rsi'].between(45, 55)) &
            (dataframe['rsi'] < self.rsi_buy_min.value)
        )

        dataframe.loc[bull_long, 'enter_long'] = 1
        dataframe.loc[bull_long, 'enter_tag'] = 'BULL_V5_ATRASO'
        dataframe.loc[lateral_long, 'enter_long'] = 1
        dataframe.loc[lateral_long, 'enter_tag'] = 'LATERAL_V5_SCALP'
        return dataframe

    def leverage(self, pair: str, current_time: datetime, current_rate: float,
                 proposed_leverage: float, max_leverage: float, side: str, **kwargs) -> float:
        # LEVERAGE DINÁMICO BULL
        # En Bull, nos permitimos ser más agresivos si la volatilidad es baja
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or dataframe.empty: return 10.0
        
        atr_rank = dataframe['btc_atr'].rolling(2016).rank(pct=True).iloc[-1]
        
        if atr_rank < 0.3: return 10.0 # Bull agresivo
        elif atr_rank < 0.7: return 7.0 # Standar
        else: return 3.0 # Protección en picos de volatilidad

    def custom_stoploss(self, pair: str, trade: Trade, current_time: datetime,
                        current_rate: float, current_profit: float, **kwargs) -> float:
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        last = dataframe.iloc[-1]
        atr_stop = (last['atr'] * float(self.stoploss_atr_mult.value)) / last['close']
        return -max(0.008, atr_stop)

    def adjust_trade_position(self, trade: Trade, current_time: datetime,
                               current_rate: float, current_profit: float, **kwargs) -> Optional[float]:
        if self.dca_enabled and current_profit < -0.04 and trade.nr_of_successful_entries < self.max_dca_orders:
            return trade.stake_amount * 1.5
        return None
