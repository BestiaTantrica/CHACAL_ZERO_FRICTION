# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
"""
CHACAL BEAR PANIC HUNTER — SOLO SHORT
Base robusta Bear + módulo Super Bear adaptativo (1m + 1h)
"""

import numpy as np
import pandas as pd
from pandas import DataFrame
from datetime import datetime
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.strategy import DecimalParameter, IStrategy, IntParameter
from freqtrade.persistence import Trade


class ChacalBear_PanicHunter(IStrategy):
    INTERFACE_VERSION = 3
    can_short: bool = True
    use_custom_exit = True
    use_custom_stoploss = True

    hyperopt_dna = {
        "BTC/USDT:USDT": {"v_factor": 4.660, "pulse_change": 0.004, "bear_roi": 0.022, "bear_sl": -0.031},
        "ETH/USDT:USDT": {"v_factor": 5.769, "pulse_change": 0.004, "bear_roi": 0.018, "bear_sl": -0.031},
        "SOL/USDT:USDT": {"v_factor": 5.386, "pulse_change": 0.001, "bear_roi": 0.042, "bear_sl": -0.040},
        "BNB/USDT:USDT": {"v_factor": 3.378, "pulse_change": 0.003, "bear_roi": 0.011, "bear_sl": -0.048},
        "XRP/USDT:USDT": {"v_factor": 5.133, "pulse_change": 0.004, "bear_roi": 0.042, "bear_sl": -0.054},
        "ADA/USDT:USDT": {"v_factor": 3.408, "pulse_change": 0.005, "bear_roi": 0.042, "bear_sl": -0.022},
        "AVAX/USDT:USDT": {"v_factor": 5.692, "pulse_change": 0.005, "bear_roi": 0.010, "bear_sl": -0.053},
        "LINK/USDT:USDT": {"v_factor": 5.671, "pulse_change": 0.005, "bear_roi": 0.038, "bear_sl": -0.041},
    }

    def informative_pairs(self):
        pairs = self.dp.current_whitelist()
        informative_pairs = [(pair, '1m') for pair in pairs]
        informative_pairs += [("BTC/USDT:USDT", "1h")]
        informative_pairs += [(pair, '1h') for pair in pairs]
        return informative_pairs

    max_open_trades = 8

    v_factor_mult = 1.323
    adx_threshold = 26
    rsi_bear_thresh = 32
    volume_mult = 1.44

    roi_base = 0.042
    rsi_kill_switch = 68
    bear_stoploss = -0.110

    rsi_1m_exit = 80
    fast_break_thresh = 0.008

    fractal_risk_threshold = DecimalParameter(0.50, 0.85, default=0.62, space='buy', optimize=True)
    super_bear_rsi = IntParameter(20, 35, default=30, space='buy', optimize=True)
    bear_logic_rsi = IntParameter(36, 45, default=40, space='buy', optimize=True)

    max_trade_duration_hours = 24
    max_loss_duration_hours = 12

    trailing_stop = True
    trailing_stop_positive = 0.015
    trailing_stop_positive_offset = 0.040
    trailing_only_offset_is_reached = True

    stoploss = -0.150
    timeframe = '5m'

    def _sl_for_pair(self, pair: str) -> float:
        return self.bear_stoploss

    def _roi_for_pair(self, pair: str) -> float:
        dna_roi = self.hyperopt_dna.get(pair, {"bear_roi": 0.03})["bear_roi"]
        return max(self.roi_base, dna_roi * 0.8)

    def _safe_series(self, dataframe: DataFrame, column: str, default: float) -> pd.Series:
        if column not in dataframe.columns:
            dataframe[column] = default
        return dataframe[column].fillna(default)

    def _clamp(self, value: float, low: float = 0.0, high: float = 1.0) -> float:
        return max(low, min(high, float(value)))

    def leverage(self, pair: str, current_time: datetime, current_rate: float,
                 proposed_leverage: float, max_leverage: float, side: str, **kwargs) -> float:
        return 5.0

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=14)
        dataframe['adx'] = ta.ADX(dataframe, timeperiod=14)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['volume_mean'] = dataframe['volume'].rolling(20).mean()
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lowerband'] = bollinger['lower']
        dataframe['bb_middleband'] = bollinger['mid']
        dataframe['price_change'] = (dataframe['close'] - dataframe['open']) / dataframe['open']
        dataframe['atr_pct_5m'] = (dataframe['atr'] / dataframe['close']).replace([np.inf, -np.inf], np.nan).fillna(0.004)
        dataframe['vol_rank_5m'] = dataframe['atr_pct_5m'].rolling(72).rank(pct=True).fillna(0.5)
        dataframe['price_change_abs_5m'] = dataframe['price_change'].abs().fillna(0.0)

        informative_1m = self.dp.get_pair_dataframe(pair=metadata['pair'], timeframe="1m")
        if not informative_1m.empty:
            informative_1m['rsi_1m'] = ta.RSI(informative_1m, timeperiod=14)
            informative_1m['price_change_1m'] = (informative_1m['close'] - informative_1m['open']) / informative_1m['open']
            informative_1m['shock_1m'] = informative_1m['price_change_1m'].abs().rolling(5).max()
            informative_1m = informative_1m[['date', 'rsi_1m', 'price_change_1m', 'shock_1m']]
            dataframe = pd.merge(dataframe, informative_1m, on='date', how='left').ffill()

        dataframe['rsi_1m'] = self._safe_series(dataframe, 'rsi_1m', 50.0)
        dataframe['price_change_1m'] = self._safe_series(dataframe, 'price_change_1m', 0.0)
        dataframe['shock_1m'] = self._safe_series(dataframe, 'shock_1m', 0.0)

        pair_1h = self.dp.get_pair_dataframe(pair=metadata['pair'], timeframe="1h")
        if pair_1h is not None and not pair_1h.empty:
            pair_1h['atr_1h'] = ta.ATR(pair_1h, timeperiod=14)
            pair_1h['atr_pct_1h'] = (pair_1h['atr_1h'] / pair_1h['close']).replace([np.inf, -np.inf], np.nan)
            pair_1h['ema21_1h'] = ta.EMA(pair_1h, timeperiod=21)
            pair_1h['dist_ema21_1h'] = ((pair_1h['ema21_1h'] - pair_1h['close']) / pair_1h['close']).replace([np.inf, -np.inf], np.nan)
            pair_1h = pair_1h[['date', 'atr_pct_1h', 'dist_ema21_1h']]
            dataframe = pd.merge(dataframe, pair_1h, on='date', how='left').ffill()

        dataframe['atr_pct_1h'] = self._safe_series(dataframe, 'atr_pct_1h', dataframe['atr_pct_5m'].rolling(12).mean().fillna(0.006))
        dataframe['dist_ema21_1h'] = self._safe_series(dataframe, 'dist_ema21_1h', 0.0)

        btc_1h = self.dp.get_pair_dataframe(pair="BTC/USDT:USDT", timeframe="1h")
        if not btc_1h.empty:
            btc_1h['ema50'] = ta.EMA(btc_1h, timeperiod=50)
            btc_1h['rsi_btc_1h'] = ta.RSI(btc_1h, timeperiod=14)
            btc_1h['atr'] = ta.ATR(btc_1h, timeperiod=14)
            btc_1h['atr_mean'] = btc_1h['atr'].rolling(8).mean()
            btc_1h['btc_atr_pct_1h'] = (btc_1h['atr'] / btc_1h['close']).replace([np.inf, -np.inf], np.nan)
            btc_1h['btc_dist_ema50'] = ((btc_1h['ema50'] - btc_1h['close']) / btc_1h['close']).replace([np.inf, -np.inf], np.nan)
        if btc_1h is not None:
            df_btc = btc_1h[['date', 'close', 'ema50', 'rsi_btc_1h', 'btc_atr_pct_1h', 'btc_dist_ema50']].copy()
            df_btc = df_btc.rename(columns={'close': 'btc_close', 'ema50': 'btc_ema50', 'rsi_btc_1h': 'btc_rsi_1h'})
            dataframe = pd.merge(dataframe, df_btc, on='date', how='left').ffill()
            btc_trend_bear = dataframe['btc_close'] < dataframe['btc_ema50']
            btc_rsi_bear = dataframe['btc_rsi_1h'] < 40
            dataframe['master_bear_switch'] = (btc_trend_bear & btc_rsi_bear).astype(int)
        else:
            dataframe['master_bear_switch'] = 0

        dataframe['btc_rsi_1h'] = self._safe_series(dataframe, 'btc_rsi_1h', 50.0)
        dataframe['btc_atr_pct_1h'] = self._safe_series(dataframe, 'btc_atr_pct_1h', 0.008)
        dataframe['btc_dist_ema50'] = self._safe_series(dataframe, 'btc_dist_ema50', 0.0)

        micro_rebound = dataframe['price_change_1m'].clip(lower=0).rolling(3).max().fillna(0.0)
        btc_weakness = ((40.0 - dataframe['btc_rsi_1h']) / 20.0).clip(0, 1)
        macro_extension = dataframe['btc_dist_ema50'].clip(lower=0).rolling(12).mean().fillna(0.0)
        pair_extension = dataframe['dist_ema21_1h'].clip(lower=0).rolling(12).mean().fillna(0.0)
        fractal_vol = (
            dataframe['atr_pct_5m'].rolling(24).rank(pct=True).fillna(0.5) * 0.35 +
            dataframe['atr_pct_1h'].rolling(24).rank(pct=True).fillna(0.5) * 0.35 +
            dataframe['btc_atr_pct_1h'].rolling(24).rank(pct=True).fillna(0.5) * 0.30
        ).clip(0, 1)
        micro_shock = (micro_rebound.rolling(12).rank(pct=True).fillna(0.0) * 0.7 + dataframe['shock_1m'].rolling(24).rank(pct=True).fillna(0.0) * 0.3).clip(0, 1)
        trend_quality = ((btc_weakness * 0.6) + macro_extension.clip(0, 1) * 0.25 + pair_extension.clip(0, 1) * 0.15).clip(0, 1)
        dataframe['fractal_risk_pressure'] = (fractal_vol * 0.45 + micro_shock * 0.35 + (1 - trend_quality) * 0.20).clip(0, 1)
        dataframe['fractal_bear_quality'] = trend_quality
        dataframe['fractal_entry_penalty'] = (dataframe['fractal_risk_pressure'] > self.fractal_risk_threshold.value).astype(int)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        pair = metadata['pair']
        dna = self.hyperopt_dna.get(pair, self.hyperopt_dna["BTC/USDT:USDT"])
        v_factor_dna = dna.get("v_factor", 1.44)
        p_change_dna = dna.get("pulse_change", 0.001)

        short_cond = (
            (dataframe['master_bear_switch'] == 1) &
            (dataframe['volume'] > (dataframe['volume_mean'] * v_factor_dna)) &
            (dataframe['price_change'] < -p_change_dna) &
            (dataframe['rsi'] < self.rsi_bear_thresh) &
            (dataframe['close'] < dataframe['bb_middleband']) &
            (dataframe['fractal_bear_quality'] > 0.35) &
            (dataframe['fractal_risk_pressure'] < 0.88) &
            ((dataframe['fractal_risk_pressure'] < self.fractal_risk_threshold.value) | (dataframe['adx'] > self.adx_threshold + 4))
        )

        dataframe.loc[short_cond, 'enter_short'] = 1
        dataframe.loc[short_cond, 'enter_tag'] = 'PANIC_HUNTER_SHORT'
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def custom_stoploss(self, pair: str, trade: 'Trade', current_time: datetime,
                        current_rate: float, current_profit: float, after_fill: bool, **kwargs) -> float:
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        base_sl = abs(self._sl_for_pair(pair))
        if dataframe is None or dataframe.empty:
            return -base_sl

        last_candle = dataframe.iloc[-1]
        atr_pct_5m = float(last_candle.get('atr_pct_5m', 0.004) or 0.004)
        atr_pct_1h = float(last_candle.get('atr_pct_1h', atr_pct_5m) or atr_pct_5m)
        frps = self._clamp(float(last_candle.get('fractal_risk_pressure', 0.5) or 0.5))
        leverage = float(getattr(trade, 'leverage', 5.0) or 5.0)

        dynamic_floor = max(base_sl * (0.70 - 0.20 * frps), atr_pct_5m * 2.2, atr_pct_1h * 1.15)
        leverage_noise = max(1.0, np.sqrt(leverage))
        dynamic_floor = dynamic_floor * (0.95 + 0.10 * leverage_noise)

        if current_profit > atr_pct_5m * 2.2:
            trail_gap = max(atr_pct_5m * 1.4, current_profit * (0.28 + 0.12 * frps))
            return -trail_gap

        return -max(dynamic_floor, base_sl * 0.55)

    def custom_exit(self, pair: str, trade: 'Trade', current_time: datetime,
                    current_rate: float, current_profit: float, **kwargs):
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        last_candle = dataframe.iloc[-1] if dataframe is not None and len(dataframe) > 0 else None

        frps = self._clamp(float(last_candle.get('fractal_risk_pressure', 0.5) if last_candle is not None else 0.5))
        bear_quality = self._clamp(float(last_candle.get('fractal_bear_quality', 0.5) if last_candle is not None else 0.5))
        roi_target = self._roi_for_pair(pair) * (1.00 - 0.35 * frps + 0.10 * bear_quality)
        roi_target = max(0.008, roi_target)
        if current_profit >= roi_target:
            return f"panic_roi_fractal_{int(frps * 100)}"

        if last_candle is not None:
            btc_rsi_1h = float(last_candle.get('btc_rsi_1h', 50.0))
            rsi_1m = float(last_candle.get('rsi_1m', 50.0))
            price_rebound_1m = float(max(last_candle.get('price_change_1m', 0.0), 0.0))
            micro_shock = float(last_candle.get('shock_1m', 0.0) or 0.0)

            if btc_rsi_1h < self.super_bear_rsi.value:
                rsi_target = self.rsi_1m_exit + 5 - int(frps * 4)
                rebound_target = self.fast_break_thresh * (1.45 - 0.25 * frps)
            elif btc_rsi_1h < self.bear_logic_rsi.value:
                rsi_target = self.rsi_1m_exit - int(frps * 4)
                rebound_target = self.fast_break_thresh * (1.10 - 0.20 * frps)
            else:
                rsi_target = self.rsi_1m_exit - int(frps * 12)
                rebound_target = self.fast_break_thresh * max(0.60, 0.85 - 0.35 * frps)

            if rsi_1m > rsi_target:
                return f"rsi_kill_1m_mod_{int(btc_rsi_1h)}"

            if price_rebound_1m > rebound_target:
                return f"fast_rebound_mod_{int(btc_rsi_1h)}"

            if micro_shock > rebound_target * 1.4 and current_profit < 0.01:
                return f"micro_shock_exit_{int(frps * 100)}"

            if btc_rsi_1h > 44 and current_profit < 0:
                return f"macro_invalidation_{int(btc_rsi_1h)}"

        trade_duration = (current_time - trade.open_date_utc).total_seconds() / 3600
        adaptive_loss_timeout = max(6.0, self.max_loss_duration_hours * (1.20 - 0.70 * frps))
        adaptive_trade_timeout = max(12.0, self.max_trade_duration_hours * (1.10 - 0.40 * frps))

        if trade_duration > adaptive_loss_timeout and current_profit < 0:
            return f"time_out_loss_fractal_{int(frps * 100)}"

        if trade_duration > adaptive_trade_timeout:
            return f"time_out_max_fractal_{int(frps * 100)}"

        return None
