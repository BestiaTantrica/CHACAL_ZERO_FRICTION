# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
"""
CHACAL SNIPER BEAR44 v4 — SOLO SHORT, FIX PARAMETROS
=====================================================
TODOS los params en spaces minimos para evitar KeyError
"""

import numpy as np
import pandas as pd
from pandas import DataFrame
from datetime import datetime, timezone
from typing import Optional, Union, Any
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.strategy import DecimalParameter, IStrategy, IntParameter
from freqtrade.persistence import Trade


class ChacalSniper_Bear44(IStrategy):
    INTERFACE_VERSION = 3
    can_short: bool = True

    def informative_pairs(self):
        return [("BTC/USDT:USDT", "1h")]

    hyperopt_dna = {
        "BTC/USDT:USDT":   {"v_factor": 4.660, "pulse_change": 0.004, "bear_roi": 0.022, "bear_sl": -0.031},
        "ETH/USDT:USDT":   {"v_factor": 5.769, "pulse_change": 0.004, "bear_roi": 0.018, "bear_sl": -0.031},
        "SOL/USDT:USDT":   {"v_factor": 5.386, "pulse_change": 0.001, "bear_roi": 0.042, "bear_sl": -0.040},
        "BNB/USDT:USDT":   {"v_factor": 3.378, "pulse_change": 0.003, "bear_roi": 0.011, "bear_sl": -0.048},
        "XRP/USDT:USDT":   {"v_factor": 5.133, "pulse_change": 0.004, "bear_roi": 0.042, "bear_sl": -0.054},
        "ADA/USDT:USDT":   {"v_factor": 3.408, "pulse_change": 0.005, "bear_roi": 0.042, "bear_sl": -0.022},
        "AVAX/USDT:USDT":  {"v_factor": 5.692, "pulse_change": 0.005, "bear_roi": 0.010, "bear_sl": -0.053},
        "LINK/USDT:USDT":  {"v_factor": 5.671, "pulse_change": 0.005, "bear_roi": 0.038, "bear_sl": -0.041},
    }

    # ================================================================
    # PARAMS — SOLO 1 space cada tipo para evitar KeyError
    # ================================================================
    max_open_trades = 8

    # --- space="buy" ---
    v_factor_mult = DecimalParameter(0.3, 2.0, decimals=3, default=1.323, space="buy", optimize=True)
    adx_threshold = IntParameter(15, 35, default=26, space="buy", optimize=True)
    rsi_bear_thresh = IntParameter(20, 50, default=32, space="buy", optimize=True)
    volume_mult = DecimalParameter(0.5, 2.5, decimals=2, default=1.44, space="buy", optimize=True)

    # --- space="sell" ---
    roi_base = DecimalParameter(0.01, 0.08, decimals=3, default=0.045, space="sell", optimize=True)
    rsi_kill_switch = IntParameter(35, 60, default=48, space="sell", optimize=True)

    # --- space="stoploss" ---
    bear_stoploss = DecimalParameter(-0.25, -0.01, decimals=3, default=-0.090, space="sell", optimize=True)

    # Trailing Stop
    trailing_stop = True
    trailing_stop_positive = 0.010
    trailing_stop_positive_offset = 0.025
    trailing_only_offset_is_reached = True

    stoploss = -0.075
    timeframe = '5m'

    def _sl_for_pair(self, pair: str) -> float:
        return self.bear_stoploss.value

    def _roi_for_pair(self, pair: str) -> float:
        dna_roi = self.hyperopt_dna.get(pair, {"bear_roi": 0.03})["bear_roi"]
        return max(self.roi_base.value, dna_roi * 0.8)

    def leverage(self, pair: str, current_time: datetime, current_rate: float,
                 proposed_leverage: float, max_leverage: float, side: str, **kwargs) -> float:
        return 5.0

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Indicadores base del par
        dataframe['adx'] = ta.ADX(dataframe, timeperiod=14)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['volume_mean'] = dataframe['volume'].rolling(20).mean()
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lowerband'] = bollinger['lower']
        dataframe['bb_middleband'] = bollinger['mid']
        dataframe['price_change'] = (dataframe['close'] - dataframe['open']) / dataframe['open']

        # --- MASTER BEAR SWITCH (BTC MACRO 1H) ---
        btc_1h = self.dp.get_pair_dataframe(pair="BTC/USDT:USDT", timeframe="1h")
        if not btc_1h.empty:
            # Resample para alinear 1h con 5m
            btc_1h['ema50'] = ta.EMA(btc_1h, timeperiod=50)
            btc_1h['atr'] = ta.ATR(btc_1h, timeperiod=14)
            btc_1h['atr_mean'] = btc_1h['atr'].rolling(8).mean()
            
            # Unimos los datos de BTC al dataframe principal
            df_btc = btc_1h[['date', 'close', 'ema50', 'atr', 'atr_mean']].copy()
            df_btc = df_btc.rename(columns={
                'close': 'btc_close',
                'ema50': 'btc_ema50',
                'atr': 'btc_atr',
                'atr_mean': 'btc_atr_mean'
            })
            dataframe = pd.merge(dataframe, df_btc, on='date', how='left').ffill()

            # Lógica del Interruptor
            btc_trend_bear = dataframe['btc_close'] < dataframe['btc_ema50']
            btc_vol_active = dataframe['btc_atr'] > dataframe['btc_atr_mean']
            dataframe['master_bear_switch'] = (btc_trend_bear & btc_vol_active).astype(int)
        else:
            dataframe['master_bear_switch'] = 1 # Fail-safe
            
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        pair = metadata['pair']
        dna = self.hyperopt_dna.get(pair, self.hyperopt_dna["BTC/USDT:USDT"])
        v_eff = dna['v_factor'] * self.v_factor_mult.value

        short_cond = (
            (dataframe['master_bear_switch'] == 1) &
            (dataframe['volume'] > (dataframe['volume_mean'] * self.volume_mult.value)) &
            (dataframe['price_change'] < -0.001) &
            (dataframe['rsi'] < self.rsi_bear_thresh.value) &
            (dataframe['rsi'] < dataframe['rsi'].shift(1)) &
            (dataframe['close'] < dataframe['bb_middleband']) &
            (dataframe['adx'] > self.adx_threshold.value)
        )

        dataframe.loc[short_cond, 'enter_short'] = 1
        dataframe.loc[short_cond, 'enter_tag'] = 'SNIPER_BEAR_SHORT'
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def custom_stoploss(self, pair: str, trade: 'Trade', current_time: datetime,
                        current_rate: float, current_profit: float, after_fill: bool, **kwargs) -> float:
        return self._sl_for_pair(pair)

    def custom_exit(self, pair: str, trade: 'Trade', current_time: datetime,
                    current_rate: float, current_profit: float, **kwargs):
        roi_target = self._roi_for_pair(pair)
        if current_profit >= roi_target:
            return "bear_roi_hit"

        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is not None and len(dataframe) > 0:
            last_candle = dataframe.iloc[-1]
            current_rsi = float(last_candle.get('rsi', 50.0))
            current_adx = float(last_candle.get('adx', 0.0))
            if current_rsi > self.rsi_kill_switch.value and current_adx > self.adx_threshold.value:
                return "rsi_kill_switch_short"
        return None