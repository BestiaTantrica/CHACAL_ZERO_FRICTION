# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
"""
CHACAL BEAR GOLD PANIC
Base Bear44 (estable) + injerto SuperBear mínimo.
"""

import pandas as pd
from pandas import DataFrame
from datetime import datetime
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.strategy import DecimalParameter, IStrategy, IntParameter
from freqtrade.persistence import Trade


class ChacalBear_GoldPanic(IStrategy):
    INTERFACE_VERSION = 3
    can_short: bool = True
    use_custom_exit = True

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

    max_open_trades = 8

    v_factor_mult = DecimalParameter(0.8, 1.8, decimals=3, default=1.323, space="buy", optimize=True)
    adx_threshold = IntParameter(18, 35, default=26, space="buy", optimize=True)
    rsi_bear_thresh = IntParameter(20, 45, default=32, space="buy", optimize=True)
    volume_mult = DecimalParameter(0.8, 2.2, decimals=2, default=1.44, space="buy", optimize=True)

    super_bear_rsi = IntParameter(18, 34, default=28, space="buy", optimize=True)

    roi_base = DecimalParameter(0.02, 0.08, decimals=3, default=0.045, space="sell", optimize=True)
    rsi_kill_switch = IntParameter(40, 75, default=52, space="sell", optimize=True)

    rsi_1m_exit = IntParameter(72, 90, default=82, space="sell", optimize=True)
    fast_break_thresh = DecimalParameter(0.006, 0.020, decimals=3, default=0.011, space="sell", optimize=True)

    bear_stoploss = DecimalParameter(-0.25, -0.02, decimals=3, default=-0.090, space="sell", optimize=True)

    max_trade_duration_hours = 24
    max_loss_duration_hours = 12

    trailing_stop = True
    trailing_stop_positive = 0.012
    trailing_stop_positive_offset = 0.045
    trailing_only_offset_is_reached = True

    stoploss = -0.150
    timeframe = '5m'

    def informative_pairs(self):
        pairs = self.dp.current_whitelist()
        informative_pairs = [(pair, '1m') for pair in pairs]
        informative_pairs += [("BTC/USDT:USDT", "1h")]
        return informative_pairs

    def _sl_for_pair(self, pair: str) -> float:
        return self.bear_stoploss.value

    def _roi_for_pair(self, pair: str) -> float:
        dna_roi = self.hyperopt_dna.get(pair, {"bear_roi": 0.03})["bear_roi"]
        return max(self.roi_base.value, dna_roi * 0.8)

    def leverage(self, pair: str, current_time: datetime, current_rate: float,
                 proposed_leverage: float, max_leverage: float, side: str, **kwargs) -> float:
        return 5.0

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['adx'] = ta.ADX(dataframe, timeperiod=14)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['volume_mean'] = dataframe['volume'].rolling(20).mean()
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_middleband'] = bollinger['mid']
        dataframe['price_change'] = (dataframe['close'] - dataframe['open']) / dataframe['open']

        informative_1m = self.dp.get_pair_dataframe(pair=metadata['pair'], timeframe="1m")
        if informative_1m is not None and not informative_1m.empty:
            informative_1m['rsi_1m'] = ta.RSI(informative_1m, timeperiod=14)
            informative_1m['price_change_1m'] = (informative_1m['close'] - informative_1m['open']) / informative_1m['open']
            informative_1m = informative_1m[['date', 'rsi_1m', 'price_change_1m']]
            dataframe = pd.merge(dataframe, informative_1m, on='date', how='left').ffill()

        if 'rsi_1m' not in dataframe.columns:
            dataframe['rsi_1m'] = 50.0
        if 'price_change_1m' not in dataframe.columns:
            dataframe['price_change_1m'] = 0.0

        btc_1h = self.dp.get_pair_dataframe(pair="BTC/USDT:USDT", timeframe="1h")
        if btc_1h is not None and not btc_1h.empty:
            btc_1h['ema50'] = ta.EMA(btc_1h, timeperiod=50)
            btc_1h['rsi_btc_1h'] = ta.RSI(btc_1h, timeperiod=14)
            btc_1h['atr'] = ta.ATR(btc_1h, timeperiod=14)
            btc_1h['atr_mean'] = btc_1h['atr'].rolling(8).mean()

            df_btc = btc_1h[['date', 'close', 'ema50', 'rsi_btc_1h', 'atr', 'atr_mean']].copy()
            df_btc = df_btc.rename(columns={
                'close': 'btc_close',
                'ema50': 'btc_ema50',
                'rsi_btc_1h': 'btc_rsi_1h',
                'atr': 'btc_atr',
                'atr_mean': 'btc_atr_mean'
            })
            dataframe = pd.merge(dataframe, df_btc, on='date', how='left').ffill()

            btc_trend_bear = dataframe['btc_close'] < dataframe['btc_ema50']
            btc_vol_active = dataframe['btc_atr'] > dataframe['btc_atr_mean']
            dataframe['master_bear_switch'] = (btc_trend_bear & btc_vol_active).astype(int)
        else:
            dataframe['master_bear_switch'] = 0
            dataframe['btc_rsi_1h'] = 50.0

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        pair = metadata['pair']
        dna = self.hyperopt_dna.get(pair, self.hyperopt_dna["BTC/USDT:USDT"])
        p_change_dna = dna.get("pulse_change", 0.001)

        # base Bear44
        base_entry = (
            (dataframe['master_bear_switch'] == 1) &
            (dataframe['volume'] > (dataframe['volume_mean'] * self.volume_mult.value)) &
            (dataframe['price_change'] < -p_change_dna) &
            (dataframe['rsi'] < self.rsi_bear_thresh.value) &
            (dataframe['close'] < dataframe['bb_middleband']) &
            (dataframe['adx'] > self.adx_threshold.value)
        )

        # super bear: más permisivo en adx/rsi para capturar pánico
        super_bear_entry = (
            (dataframe['master_bear_switch'] == 1) &
            (dataframe['btc_rsi_1h'] < self.super_bear_rsi.value) &
            (dataframe['volume'] > (dataframe['volume_mean'] * max(1.0, self.volume_mult.value - 0.15))) &
            (dataframe['price_change'] < -p_change_dna) &
            (dataframe['rsi'] < (self.rsi_bear_thresh.value + 4)) &
            (dataframe['close'] < dataframe['bb_middleband'])
        )

        dataframe.loc[base_entry, 'enter_short'] = 1
        dataframe.loc[base_entry, 'enter_tag'] = 'BEAR_BASE'

        dataframe.loc[super_bear_entry, 'enter_short'] = 1
        dataframe.loc[super_bear_entry, 'enter_tag'] = 'SUPER_BEAR'
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
            btc_rsi_1h = float(last_candle.get('btc_rsi_1h', 50.0))
            rsi_1m = float(last_candle.get('rsi_1m', 50.0))
            rebound_1m = float(max(last_candle.get('price_change_1m', 0.0), 0.0))

            if btc_rsi_1h < self.super_bear_rsi.value:
                # En pánico, dejar respirar
                rsi_target = self.rsi_1m_exit.value + 4
                rebound_target = self.fast_break_thresh.value * 1.6
            else:
                rsi_target = self.rsi_1m_exit.value
                rebound_target = self.fast_break_thresh.value

            if rsi_1m > rsi_target:
                return f"rsi_1m_kill_{int(btc_rsi_1h)}"

            if rebound_1m > rebound_target:
                return f"rebound_1m_kill_{int(btc_rsi_1h)}"

            current_rsi = float(last_candle.get('rsi', 50.0))
            current_adx = float(last_candle.get('adx', 0.0))
            if btc_rsi_1h >= self.super_bear_rsi.value and current_rsi > self.rsi_kill_switch.value and current_adx > self.adx_threshold.value:
                return "rsi_kill_switch_short"

        trade_duration = (current_time - trade.open_date_utc).total_seconds() / 3600
        if trade_duration > self.max_loss_duration_hours and current_profit < 0:
            return "time_out_loss_12h"
        if trade_duration > self.max_trade_duration_hours:
            return "time_out_max_24h"
        return None
