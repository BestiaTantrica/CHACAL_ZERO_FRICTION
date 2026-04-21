# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
"""
CHACAL SNIPER BEAR V5 — ELITE DUAL BOREDOM
==========================================
- Mejoras: 
    1. Cache de BTC para reducir OOM.
    2. Fuzzy Logic para el Master Switch.
    3. Leverage Dinámico ATR-Based.
    4. Airbag 1m con Body Ratio (3 de 4 velas).
    5. Prioridad de SL DNA.
    6. Kill Switch Institucional (RSI 1m > 85 o 48h timeout).
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


class ChacalSniper_BearV5(IStrategy):
    INTERFACE_VERSION = 3
    can_short: bool = True

    def informative_pairs(self):
        pairs = self.dp.current_whitelist()
        informative = [(pair, "1m") for pair in pairs]
        informative += [("BTC/USDT:USDT", "1h"), ("BTC/USDT:USDT", "5m"), ("BTC/USDT:USDT", "1m")]
        return informative

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
    # PARAMS
    # ================================================================
    max_open_trades = 8
    v_factor_mult = DecimalParameter(0.3, 2.0, decimals=3, default=1.323, space="buy", optimize=True)
    adx_threshold = IntParameter(15, 35, default=26, space="buy", optimize=True)
    rsi_bear_thresh = IntParameter(20, 50, default=32, space="buy", optimize=True)
    volume_mult = DecimalParameter(0.5, 2.5, decimals=2, default=1.44, space="buy", optimize=True)

    roi_base = DecimalParameter(0.01, 0.08, decimals=3, default=0.045, space="sell", optimize=True)
    kill_rsi_1h = IntParameter(40, 70, default=55, space="sell", optimize=True)
    kill_rsi_5m = IntParameter(50, 80, default=65, space="sell", optimize=True)
    rsi_kill_switch = IntParameter(60, 90, default=75, space="sell", optimize=True)
    bear_stoploss = DecimalParameter(-0.15, -0.06, decimals=3, default=-0.090, space="sell", optimize=True)

    # Trailing Stop
    trailing_stop = True
    trailing_stop_positive = 0.010
    trailing_stop_positive_offset = 0.025
    trailing_only_offset_is_reached = True

    stoploss = -0.99 
    timeframe = '5m'
    startup_candle_count = 1200

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Indicadores base del par
        dataframe['adx'] = ta.ADX(dataframe, timeperiod=14)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['volume_mean'] = dataframe['volume'].rolling(20).mean()
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_middleband'] = bollinger['mid']
        dataframe['price_change'] = (dataframe['close'] - dataframe['open']) / dataframe['open']

        # 1. FUZZY LOGIC PARA BTC (REDUCCIÓN OOM)
        btc_1h = self.dp.get_pair_dataframe(pair="BTC/USDT:USDT", timeframe="1h")
        if not btc_1h.empty:
            btc_1h['btc_rsi_1h'] = ta.RSI(btc_1h, timeperiod=14)
            btc_1h['ema50'] = ta.EMA(btc_1h, timeperiod=50)
            btc_1h['atr'] = ta.ATR(btc_1h, timeperiod=14)
            btc_1h['atr_mean'] = btc_1h['atr'].rolling(8).mean()
            
            df_btc = btc_1h[['date', 'close', 'ema50', 'atr', 'atr_mean', 'btc_rsi_1h']].copy()
            df_btc = df_btc.rename(columns={
                'close': 'btc_close',
                'ema50': 'btc_ema50',
                'atr': 'btc_atr',
                'atr_mean': 'btc_atr_mean'
            })
            dataframe = pd.merge(dataframe, df_btc, on='date', how='left').ffill()

            # FUZZY CALCULUS
            ema_dist = ((dataframe['btc_ema50'] - dataframe['btc_close']) / dataframe['btc_ema50']).clip(0, 0.05) / 0.05
            vol_strength = ((dataframe['btc_atr'] - dataframe['btc_atr_mean']) / dataframe['btc_atr_mean']).clip(0, 1)
            rsi_strength = (1 - dataframe['btc_rsi_1h'] / 100)
            dataframe['bear_strength'] = (0.4 * ema_dist + 0.3 * vol_strength + 0.3 * rsi_strength)
            dataframe['master_bear_switch'] = 1
        else:
            dataframe['master_bear_switch'] = 1
            dataframe['btc_rsi_1h'] = 50

        # BTC 5m y 1m
        btc_5m = self.dp.get_pair_dataframe(pair="BTC/USDT:USDT", timeframe="5m")
        if not btc_5m.empty:
             dataframe['btc_rsi_5m'] = ta.RSI(btc_5m, timeperiod=14)

        btc_1m = self.dp.get_pair_dataframe(pair="BTC/USDT:USDT", timeframe="1m")
        if btc_1m is not None and not btc_1m.empty:
            btc_1m['btc_rsi_1m'] = ta.RSI(btc_1m, timeperiod=14)
            dataframe = pd.merge_asof(
                dataframe.sort_values('date'),
                btc_1m[['date', 'btc_rsi_1m']].sort_values('date'),
                on='date', direction='backward'
            )

        # 2. AIRBAG 1m MEJORADO (Body Ratio + 3 de 4)
        inf_1m = self.dp.get_pair_dataframe(pair=metadata['pair'], timeframe="1m")
        if inf_1m is not None and not inf_1m.empty:
            inf_1m = inf_1m.copy()
            inf_1m['rsi_1m'] = ta.RSI(inf_1m, timeperiod=14)
            inf_1m['ema_slow_1m'] = ta.EMA(inf_1m, timeperiod=50)
            inf_1m['vol_mean_1m'] = inf_1m['volume'].rolling(10).mean()
            inf_1m['body_ratio'] = abs(inf_1m['close'] - inf_1m['open']) / (inf_1m['high'] - inf_1m['low']).replace(0, 0.0001)
            
            pump_signal = (
                (inf_1m['close'] > inf_1m['ema_slow_1m']) & 
                (inf_1m['volume'] > inf_1m['vol_mean_1m'] * 1.5) & 
                (inf_1m['body_ratio'] > 0.6)
            ).astype(int)
            
            inf_1m['pair_airbag_short_trigger'] = (pump_signal.rolling(4).sum() >= 3).astype(int)
            inf_1vars = inf_1m[['date', 'rsi_1m', 'pair_airbag_short_trigger']].rename(columns={'rsi_1m': 'pair_rsi_1m'})
            dataframe = pd.merge_asof(
                dataframe.sort_values('date'),
                inf_1vars.sort_values('date'),
                on='date', direction='backward'
            )
            
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        short_cond = (
            (dataframe['master_bear_switch'] == 1) &
            (dataframe['volume'] > (dataframe['volume_mean'] * self.volume_mult.value)) &
            (dataframe['price_change'] < -0.001) &
            (dataframe['rsi'] < self.rsi_bear_thresh.value) &
            (dataframe['close'] < dataframe['bb_middleband']) &
            (dataframe['adx'] > self.adx_threshold.value)
        )
        dataframe.loc[short_cond, 'enter_short'] = 1
        dataframe.loc[short_cond, 'enter_tag'] = 'SNIPER_BEAR_V5'
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def custom_stoploss(self, pair: str, trade: 'Trade', current_time: datetime,
                        current_rate: float, current_profit: float, **kwargs) -> float:
        dna_sl = self.hyperopt_dna.get(pair, {}).get("bear_sl")
        if dna_sl: return dna_sl
        return float(self.bear_stoploss.value)

    def custom_exit(self, pair: str, trade: 'Trade', current_time: datetime,
                    current_rate: float, current_profit: float, **kwargs):
        
        dna_roi = self.hyperopt_dna.get(pair, {"bear_roi": 0.03})["bear_roi"]
        if current_profit >= dna_roi:
            return "bear_roi_hit"

        open_minutes = (current_time - trade.open_date_utc).total_seconds() / 60.0
        
        # ── KILL SWITCH INSTITUCIONAL (Cero Zombies) ──────────────────────
        # 1. Timeout 48h
        if open_minutes > 2880:
            return "kill_switch_48h"

        if current_profit > -0.01:
            return None

        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is not None and not dataframe.empty:
            last_candle = dataframe.iloc[-1]
            # 2. RSI 1m Extremo
            last_rsi_1m = last_candle.get('pair_rsi_1m', 0)
            if last_rsi_1m > 85:
                return "kill_switch_rsi_1m_85"

            # Airbag V5
            if last_candle.get('pair_airbag_short_trigger', 0) == 1:
                return "airbag_1m_pump_elite"

            # Cascada RSI
            btc_rsi_1h = last_candle.get('btc_rsi_1h', 50)
            btc_rsi_5m = last_candle.get('btc_rsi_5m', 50)
            btc_rsi_1m = last_candle.get('btc_rsi_1m', 50)
            if btc_rsi_1h > self.kill_rsi_1h.value and btc_rsi_5m > self.kill_rsi_5m.value and btc_rsi_1m > self.rsi_kill_switch.value:
                return "airbag_cascada_v5"

        return None

    def leverage(self, pair: str, current_time: datetime, current_rate: float,
                 proposed_leverage: float, max_leverage: float, side: str, **kwargs) -> float:
        # LEVERAGE DINÁMICO ATR-BASED (Elite)
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or dataframe.empty: return 5.0
        atr_rank = dataframe['btc_atr'].rolling(2016).rank(pct=True).iloc[-1]
        
        if atr_rank < 0.3: return 7.0 # Calma relativa
        elif atr_rank < 0.6: return 5.0 # Normal
        else: return 3.0 # Protección
