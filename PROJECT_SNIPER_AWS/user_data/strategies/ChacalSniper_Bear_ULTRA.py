# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
"""
CHACAL SNIPER BEAR ULTRA — SOLO SHORT, DNA 168% + KILL SWITCH 1m
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


class ChacalSniper_Bear_ULTRA(IStrategy):
    INTERFACE_VERSION = 3
    can_short: bool = True

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

    def informative_pairs(self):
        pairs = self.dp.current_whitelist()
        informative_pairs = [(pair, '1m') for pair in pairs]
        informative_pairs += [("BTC/USDT:USDT", "1h")]
        return informative_pairs

    max_open_trades = 8

    v_factor_mult = 1.323
    adx_threshold = 26
    rsi_bear_thresh = 32
    volume_mult = 1.44

    # --- MODO CHACAL AGRESIVO (ÉPOCA 7 - PROFIT 38%) ---
    roi_base = 0.042
    rsi_kill_switch = 68
    bear_stoploss = -0.110

    # --- PROTECCIÓN QUIRÚRGICA 1M (MODO AGRESIVO) ---
    rsi_1m_exit = 80
    fast_break_thresh = 0.008  # 0.8% rebote en 1m es suficiente para huir

    # --- PROTOCOLO ANTI-ZOMBIE ---
    max_trade_duration_hours = 24
    max_loss_duration_hours = 12

    trailing_stop = True
    trailing_stop_positive = 0.015
    trailing_stop_positive_offset = 0.040 # Un poco más ajustado
    trailing_only_offset_is_reached = True

    stoploss = -0.150
    timeframe = '5m'

    def _sl_for_pair(self, pair: str) -> float:
        return self.bear_stoploss

    def _roi_for_pair(self, pair: str) -> float:
        dna_roi = self.hyperopt_dna.get(pair, {"bear_roi": 0.03})["bear_roi"]
        return max(self.roi_base, dna_roi * 0.8)

    def leverage(self, pair: str, current_time: datetime, current_rate: float,
                 proposed_leverage: float, max_leverage: float, side: str, **kwargs) -> float:
        return 5.0

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Indicadores timeframe principal (5m)
        dataframe['adx'] = ta.ADX(dataframe, timeperiod=14)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['volume_mean'] = dataframe['volume'].rolling(20).mean()
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lowerband'] = bollinger['lower']
        dataframe['bb_middleband'] = bollinger['mid']
        dataframe['price_change'] = (dataframe['close'] - dataframe['open']) / dataframe['open']

        # --- DATOS 1M (EL FINO) ---
        informative_1m = self.dp.get_pair_dataframe(pair=metadata['pair'], timeframe="1m")
        if not informative_1m.empty:
            informative_1m['rsi_1m'] = ta.RSI(informative_1m, timeperiod=14)
            informative_1m['price_change_1m'] = (informative_1m['close'] - informative_1m['open']) / informative_1m['open']
            
            # Renombramos para evitar colisiones y mergeamos
            informative_1m = informative_1m[['date', 'rsi_1m', 'price_change_1m']]
            dataframe = pd.merge(dataframe, informative_1m, on='date', how='left').ffill()

        # --- MASTER BEAR SWITCH (BTC MACRO 1H) ---
        btc_1h = self.dp.get_pair_dataframe(pair="BTC/USDT:USDT", timeframe="1h")
        if not btc_1h.empty:
            btc_1h['ema50'] = ta.EMA(btc_1h, timeperiod=50)
            btc_1h['rsi_btc_1h'] = ta.RSI(btc_1h, timeperiod=14)
            btc_1h['atr'] = ta.ATR(btc_1h, timeperiod=14)
            btc_1h['atr_mean'] = btc_1h['atr'].rolling(8).mean()
        if btc_1h is not None:
            df_btc = btc_1h[['date', 'close', 'ema50', 'rsi_btc_1h']].copy()
            df_btc = df_btc.rename(columns={
                'close': 'btc_close',
                'ema50': 'btc_ema50',
                'rsi_btc_1h': 'btc_rsi_1h'
            })
            dataframe = pd.merge(dataframe, df_btc, on='date', how='left').ffill()
            btc_trend_bear = dataframe['btc_close'] < dataframe['btc_ema50']
            btc_rsi_bear = dataframe['btc_rsi_1h'] < 40  # CANDADO ANTI-BULL: BTC debe estar débil
            
            dataframe['master_bear_switch'] = (btc_trend_bear & btc_rsi_bear).astype(int)
        else:
            dataframe['master_bear_switch'] = 0 # No hay datos BTC = No operamos por seguridad

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        pair = metadata['pair']
        dna = self.hyperopt_dna.get(pair, self.hyperopt_dna["BTC/USDT:USDT"])
        
        # RECONEXIÓN CON ADN 168% POR PAR
        v_factor_dna = dna.get("v_factor", 1.44)
        p_change_dna = dna.get("pulse_change", 0.001)

        short_cond = (
            (dataframe['master_bear_switch'] == 1) &
            (dataframe['volume'] > (dataframe['volume_mean'] * v_factor_dna)) &
            (dataframe['price_change'] < -p_change_dna) &
            (dataframe['rsi'] < self.rsi_bear_thresh) &
            (dataframe['close'] < dataframe['bb_middleband'])
        )

        dataframe.loc[short_cond, 'enter_short'] = 1
        dataframe.loc[short_cond, 'enter_tag'] = 'SNIPER_ULTRA_FIRE'
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
            
            # --- KILL SWITCH 1M (RE-ACTIVADO) ---
            # --- MODO ADAPTATIVO ---
            btc_rsi_1h = float(last_candle.get('btc_rsi_1h', 50.0))
            
            # MODO SUPER BEAR (BTC rsi < 30): Dejamos correr un poco más
            if btc_rsi_1h < 30:
                rsi_target = self.rsi_1m_exit + 5 # Más tolerancia (85)
                rebound_target = self.fast_break_thresh * 1.5 # Más aire (1.2%)
            else:
                # MODO NORMAL/AMAGADOR: Máximo rigor
                rsi_target = self.rsi_1m_exit
                rebound_target = self.fast_break_thresh

            if rsi_1m > rsi_target:
                return f"rsi_kill_1m_mod_{int(btc_rsi_1h)}"
            
            if price_rebound_1m > rebound_target:
                return f"fast_rebound_mod_{int(btc_rsi_1h)}"

        # --- GESTIÓN DE TIEMPO (ANTI-ZOMBIE) ---
        trade_duration = (current_time - trade.open_date_utc).total_seconds() / 3600
        
        # Si lleva más de 12h en pérdida, fuera.
        if trade_duration > self.max_loss_duration_hours and current_profit < 0:
            return "time_out_loss_12h"
            
        # Si lleva más de 24h, fuera pase lo que pase.
        if trade_duration > self.max_trade_duration_hours:
            return "time_out_max_24h"
                
        return None

