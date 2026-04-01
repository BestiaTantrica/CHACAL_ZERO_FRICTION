# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
"""
CHACAL VOLUME HUNTER - PC EDITION
=================================
- BASADA EN: Chacal_Adaptive_V3 (AWS LOGIC)
- ENFOQUE: BULL / LATERAL con VOLUMEN REAL
- MOTOR: Correlación con BTC + Atraso Reversión
- ESPECIFICA PARA PC: Sin modo Escudo Bear (el servidor se encarga de eso)
"""
import numpy as np
import pandas as pd
from pandas import DataFrame
from datetime import datetime, timedelta
from typing import Optional, Any, Dict
import talib.abstract as ta
from freqtrade.strategy import IStrategy, DecimalParameter, IntParameter
from freqtrade.persistence import Trade

class ChacalVolumeHunter_V1(IStrategy):
    INTERFACE_VERSION = 3
    can_short = False # SOLO LONGS en PC (Bull/Lateral)
    use_custom_exit = True
    use_custom_stoploss = True
    position_adjustment_enable = True

    # --- HYPEROPTABLE PARAMETERS (OPTIMIZADOS PARA BULL) ---
    stoploss_atr_mult = DecimalParameter(0.8, 1.5, default=1.1, space='sell', load=True)
    rsi_buy_min = IntParameter(15, 35, default=21, space='buy', load=True)
    btc_threshold_mult = DecimalParameter(0.8, 2.0, default=1.15, space='buy', load=True)

    # DCA Control para recuperación de retrocesos en Bull
    dca_enabled = True
    max_dca_orders = 2
    dca_drop_mult = DecimalParameter(1.5, 3.0, default=2.1, space='buy', load=True)

    # --- VOLUMEN Y CORRELACIÓN (DNA V3) ---
    w_corr  = DecimalParameter(0.30, 0.60, default=0.45, space='buy', load=True)
    w_atr   = DecimalParameter(0.10, 0.40, default=0.20, space='buy', load=True)
    corr_window = 144 # 12 horas en 5m
    
    stoploss = -0.99 
    timeframe = '5m'
    inf_timeframe = '1h'
    max_open_trades = 6 # Limitado para concentrar volumen en las mejores 6
    startup_candle_count: int = 144

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # BASE INDICATORS
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=14)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['volume_mean'] = dataframe['volume'].rolling(20).mean()
        
        # BTC Data for Correlation
        btc_df_5m = self.dp.get_pair_dataframe(pair="BTC/USDT:USDT", timeframe=self.timeframe)
        if btc_df_5m is not None and not btc_df_5m.empty:
            dataframe['btc_5m_rsi'] = ta.RSI(btc_df_5m, timeperiod=14)
            dataframe['btc_5m_close'] = btc_df_5m['close']
            dataframe['btc_5m_std'] = btc_df_5m['close'].pct_change().rolling(24).std()
        else:
            dataframe['btc_5m_rsi'] = 50
            dataframe['btc_5m_close'] = dataframe['close']
            dataframe['btc_5m_std'] = 0.002

        # Atraso Real vs BTC (Lógica V3 que está dando profit)
        dataframe['atraso_real'] = dataframe['btc_5m_close'].pct_change(5) - dataframe['close'].pct_change(5)
        
        # Correlación (Protección contra desacoples peligrosos)
        btc_ret = dataframe['btc_5m_close'].pct_change()
        pair_ret = dataframe['close'].pct_change()
        dataframe['corr_btc'] = pair_ret.rolling(self.corr_window).corr(btc_ret).fillna(0.8)

        # Risk Pressure Score (Para Bull Hunter)
        atr_pct = dataframe['atr'] / dataframe['close']
        atr_roll = atr_pct.rolling(self.corr_window).rank(pct=True).fillna(0.5)
        corr_inv = (1 - dataframe['corr_btc']).clip(0, 1)
        
        dataframe['risk_pressure_score'] = (
            float(self.w_corr.value) * corr_inv + 
            float(self.w_atr.value) * atr_roll
        ).clip(0, 1)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dynamic_threshold = dataframe['btc_5m_std'] * float(self.btc_threshold_mult.value)
        
        # Filtro de Calidad (Solo si hay volumen alto y riesgo bajo)
        volume_guard = dataframe['volume'] > (dataframe['volume_mean'] * 1.2)
        risk_guard = dataframe['risk_pressure_score'] < 0.40 # Solo entra si no hay "presión de desacople" (Bull saludable)

        # Lógica BULL ATRASO (Efectiva en AWS)
        bull_long = (
            (dataframe['btc_5m_rsi'] > 55) & # BTC confirmando Bull
            (dataframe['atraso_real'] > dynamic_threshold) &
            (dataframe['atraso_real'].shift(1) <= dynamic_threshold) &
            volume_guard &
            risk_guard
        )

        # Lógica LATERAL RSI
        lateral_long = (
            (dataframe['btc_5m_rsi'].between(45, 55)) &
            (dataframe['rsi'] < self.rsi_buy_min.value) &
            volume_guard
        )

        dataframe.loc[bull_long, 'enter_long'] = 1
        dataframe.loc[bull_long, 'enter_tag'] = 'BULL_VOLUME_ATRASO'
        
        dataframe.loc[lateral_long, 'enter_long'] = 1
        dataframe.loc[lateral_long, 'enter_tag'] = 'LATERAL_VOLUME_SCALP'

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Salida por profit técnico RSI
        dataframe.loc[dataframe['rsi'] > 75, 'exit_long'] = 1
        return dataframe

    def custom_stoploss(self, pair: str, trade: Trade, current_time: datetime,
                        current_rate: float, current_profit: float, **kwargs) -> float:
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or dataframe.empty: return self.stoploss
        
        last = dataframe.iloc[-1]
        atr_stop = (last['atr'] * float(self.stoploss_atr_mult.value)) / last['close']
        
        # Si estamos en racha de profit Bull, apretar el stop
        if current_profit > 0.03:
            return -0.015
            
        return -max(0.02, atr_stop) # Nunca menos del 2% por ruido en PC

    def adjust_trade_position(self, trade: Trade, current_time: datetime,
                               current_rate: float, current_profit: float,
                               min_stake: Optional[float], max_stake: float,
                               current_entry_rate: float, **kwargs) -> Optional[float]:
        # DCA de recuperación solo en mercados con volumen
        if not self.dca_enabled or current_profit > -0.03:
            return None
        
        if trade.nr_of_successful_entries < self.max_dca_orders:
            return trade.stake_amount * 1.5
            
        return None
