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
        return [("BTC/USDT:USDT", "1h"), ("BTC/USDT:USDT", "1m")]

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
    
    # Cascada RSI para el Airbag de 1m (Fino Multi-temporidad)
    kill_rsi_1h = IntParameter(40, 70, default=55, space="sell", optimize=True)
    kill_rsi_5m = IntParameter(50, 80, default=65, space="sell", optimize=True)
    rsi_kill_switch = IntParameter(60, 90, default=75, space="sell", optimize=True) # RSI de 1m

    # --- space="stoploss" ---
    # Rango profundo (-6% a -15%) para forzar a Hyperopt a crear una red de seguridad, no una salida temprana.
    bear_stoploss = DecimalParameter(-0.15, -0.06, decimals=3, default=-0.090, space="sell", optimize=True)

    # Trailing Stop
    trailing_stop = True
    trailing_stop_positive = 0.010
    trailing_stop_positive_offset = 0.025
    trailing_only_offset_is_reached = True

    stoploss = -0.12 # Red de seguridad final
    timeframe = '5m'

    def _hardened_bear_sl(self, pair: str) -> float:
        dna_sl = self.hyperopt_dna.get(pair, {"bear_sl": -0.09})["bear_sl"]
        hard_caps = {
            "ADA/USDT:USDT": -0.022,
            "BNB/USDT:USDT": -0.048,
        }
        if pair in hard_caps:
            dna_sl = max(dna_sl, hard_caps[pair])
            if self.dp:
                btc_1h = self.dp.get_pair_dataframe(pair="BTC/USDT:USDT", timeframe="1h")
                if btc_1h is not None and not btc_1h.empty:
                    btc_1h = btc_1h.copy()
                    btc_1h['atr'] = ta.ATR(btc_1h, timeperiod=14)
                    btc_1h['atr_mean'] = btc_1h['atr'].rolling(8).mean()
                    last = btc_1h.iloc[-1]
                    if pd.notna(last.get('atr')) and pd.notna(last.get('atr_mean')) and float(last['atr']) > float(last['atr_mean']):
                        dna_sl *= 0.9
        return dna_sl

    def _sl_for_pair(self, pair: str) -> float:
        return self._hardened_bear_sl(pair)

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

        btc_1h = self.dp.get_pair_dataframe(pair="BTC/USDT:USDT", timeframe="1h")
        if not btc_1h.empty:
            # Resample para alinear 1h con 5m
            btc_1h['btc_rsi_1h'] = ta.RSI(btc_1h, timeperiod=14)
            btc_1h['ema50'] = ta.EMA(btc_1h, timeperiod=50)
            btc_1h['atr'] = ta.ATR(btc_1h, timeperiod=14)
            btc_1h['atr_mean'] = btc_1h['atr'].rolling(8).mean()
            
            # Unimos los datos de BTC al dataframe principal
            df_btc = btc_1h[['date', 'close', 'ema50', 'atr', 'atr_mean', 'btc_rsi_1h']].copy()
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
            dataframe['btc_rsi_1h'] = 50

        # DataFrame RSI BTC 5m para la Cascada
        dataframe['btc_rsi_5m'] = dataframe['rsi'] # Como proxy usamos el rsi del par en 5m, o calculamos sobre btc
        btc_5m = self.dp.get_pair_dataframe(pair="BTC/USDT:USDT", timeframe="5m")
        if not btc_5m.empty:
             dataframe['btc_rsi_5m'] = ta.RSI(btc_5m, timeperiod=14)

        btc_1m = self.dp.get_pair_dataframe(pair="BTC/USDT:USDT", timeframe="1m")
        if btc_1m is not None and not btc_1m.empty:
            btc_1m = btc_1m.copy()
            btc_1m['btc_rsi_1m'] = ta.RSI(btc_1m, timeperiod=14)
            df_btc_1m = btc_1m[['date', 'btc_rsi_1m']].copy()
            dataframe = pd.merge_asof(
                dataframe.sort_values('date'),
                df_btc_1m.sort_values('date'),
                on='date',
                direction='backward'
            )
        else:
            dataframe['btc_rsi_1m'] = np.nan
        
        # --- MICRO / MIRA INSTITUCIONAL (1m) del Par Activo ---
        inf_1m = self.dp.get_pair_dataframe(pair=metadata['pair'], timeframe="1m")
        
        if inf_1m is not None and not inf_1m.empty:
            inf_1m = inf_1m.copy()
            inf_1m['rsi_1m'] = ta.RSI(inf_1m, timeperiod=14)
            inf_1m['ema_slow_1m'] = ta.EMA(inf_1m, timeperiod=50)
            inf_1m['vol_mean_1m'] = inf_1m['volume'].rolling(10).mean()
            
            # Airbag Persistencia (3 velas por encima de EMA con volumen)
            inf_1m['airbag_short_trigger'] = ((inf_1m['close'] > inf_1m['ema_slow_1m']) & (inf_1m['volume'] > inf_1m['vol_mean_1m'])).rolling(3).min()
            
            # Componentes adicionales para el scoring
            inf_1m['pa_bearish'] = (inf_1m['close'] < inf_1m['open']).astype(int)
            inf_1m['exhaust_short'] = (inf_1m['rsi_1m'] > 70).astype(int)
            inf_1m['div_bearish'] = ((inf_1m['close'] >= inf_1m['close'].shift(1)) & (inf_1m['rsi_1m'] < inf_1m['rsi_1m'].shift(1))).astype(int)
            
            inf_1m_vars = inf_1m[['date', 'rsi_1m', 'ema_slow_1m', 'vol_mean_1m', 'airbag_short_trigger', 'pa_bearish', 'exhaust_short', 'div_bearish']]
            inf_1m_vars = inf_1m_vars.rename(columns={'rsi_1m': 'pair_rsi_1m', 'airbag_short_trigger': 'pair_airbag_short_trigger'})
            
            dataframe = pd.merge_asof(
                dataframe.sort_values('date'),
                inf_1m_vars.sort_values('date'),
                on='date',
                direction='backward'
            )
            
            # Construcción del SCORING (opcional, para la entrada)
            dataframe['score_short'] = dataframe['pa_bearish'] + dataframe['exhaust_short'] + dataframe['div_bearish']
            
        else:
            dataframe['pair_rsi_1m'] = np.nan
            dataframe['pair_airbag_short_trigger'] = 0
            dataframe['score_short'] = 0
            
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

        # ── SALIDA 1: ROI alcanzado (la salida feliz) ──────────────────────
        roi_target = self._roi_for_pair(pair)
        if current_profit >= roi_target:
            return "bear_roi_hit"

        # ── SALIDA 2: AIRBAG DE 1m (El Fino Institucional) ─────────────────
        # GUARDA 1: El trade lleva más de 60 min abierto.
        #           Si recién arrancó, el 1m no interfiere.
        open_minutes = 0.0
        if trade.open_date_utc:
            open_minutes = (current_time - trade.open_date_utc).total_seconds() / 60.0
        if open_minutes < 60:
            return None

        # GUARDA 2: Estamos en pérdida real (>1%).
        #           Si vamos ganando o casi en cero, el bot no corta nada.
        if current_profit > -0.01:
            return None

        # GUARDA 3: Cascada RSI (RSI Macro alcista -> RSI Medio alcista -> Cruce RSI 1m)
        # Esto previene salidas por ruido de 1m en tendencias bajistas sanas.
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is not None and len(dataframe) > 1:
            last_candle = dataframe.iloc[-1]
            btc_rsi_1m_now  = float(last_candle.get('btc_rsi_1m', np.nan))
            btc_rsi_1m_prev = float(dataframe.iloc[-2].get('btc_rsi_1m', np.nan))
            btc_rsi_5m_now  = float(last_candle.get('btc_rsi_5m', np.nan))
            btc_rsi_1h_now  = float(last_candle.get('btc_rsi_1h', np.nan))
            airbag_trigger = last_candle.get('pair_airbag_short_trigger', 0)

            # NUEVO AIRBAG CUÁNTICO (Salva la cuenta si el par hace un breakout real alcista)
            if airbag_trigger == 1:
                return "airbag_1m_pump_real"

            if pd.notna(btc_rsi_1m_now) and pd.notna(btc_rsi_1m_prev) and pd.notna(btc_rsi_5m_now) and pd.notna(btc_rsi_1h_now):
                # Evaluación en Cascada
                macro_bull = btc_rsi_1h_now > self.kill_rsi_1h.value
                micro_bull = btc_rsi_5m_now > self.kill_rsi_5m.value
                cruce_1m_violento = (btc_rsi_1m_prev <= self.rsi_kill_switch.value) and (btc_rsi_1m_now > self.rsi_kill_switch.value)

                # Si el rebote se sincroniza en todas las temporalidades (peligro extremo)
                if macro_bull and micro_bull and cruce_1m_violento:
                    return "airbag_cascada_rebote_violento"

        return None