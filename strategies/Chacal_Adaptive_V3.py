# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
"""
CHACAL ADAPTIVE V3
==================
- MOTOR DE ESTADOS: NORMAL, ALERTA, REBELDE_LONG, PIVOT_SHORT, RECOVERY
- SCORES HYPEROPTABLES: Risk Pressure & Pivot Short
- CONTINGENCIA: Oveja Descarriada (Stoploss dinámico por estado)
- PIVOTE: Entrada automática en Short si el par se desacopla y confirma tendencia bajista
"""
import numpy as np
import pandas as pd
from pandas import DataFrame
from datetime import datetime, timedelta
from typing import Optional, Any, Dict
import talib.abstract as ta
from freqtrade.strategy import IStrategy, DecimalParameter, IntParameter
from freqtrade.persistence import Trade

class Chacal_Adaptive_V3(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    use_custom_exit = True
    use_custom_stoploss = True
    position_adjustment_enable = True

    # --- HYPEROPTABLE PARAMETERS (ENTRADA V2) ---
    stoploss_atr_mult = DecimalParameter(0.5, 2.0, default=0.964, space='sell', load=True)
    rsi_buy_min = IntParameter(10, 40, default=19, space='buy', load=True)
    rsi_buy_max = IntParameter(60, 90, default=71, space='buy', load=True)
    btc_threshold_mult = DecimalParameter(0.5, 2.5, default=1.21, space='buy', load=True)

    # Parametros DCA
    dca_enabled = True
    max_dca_orders = IntParameter(1, 4, default=1, space='buy', load=True)
    dca_drop_mult = DecimalParameter(1.0, 4.0, default=1.805, space='buy', load=True)

    # --- HYPEROPTABLE PARAMETERS (V3 ADAPTIVE) ---
    # Weights del Risk Score
    w_corr  = DecimalParameter(0.10, 0.70, default=0.485, space='buy', load=True)
    w_div   = DecimalParameter(0.10, 0.90, default=0.543, space='buy', load=True)
    w_atr   = DecimalParameter(0.05, 0.40, default=0.254, space='buy', load=True)
    corr_window = IntParameter(96, 480, default=288, space='buy', load=True)
    short_score_floor_mult = DecimalParameter(0.20, 0.90, default=0.50, space='buy', load=True)
    long_risk_guard_factor = DecimalParameter(0.60, 1.00, default=0.85, space='buy', load=True)

    # Weights del Pivot Score
    w_rps   = DecimalParameter(0.30, 0.70, default=0.692, space='buy', load=True)
    w_ema   = DecimalParameter(0.10, 0.50, default=0.324, space='buy', load=True)
    w_macro = DecimalParameter(0.05, 0.40, default=0.23, space='buy', load=True)

    # Umbrales de transición
    alerta_threshold  = DecimalParameter(0.30, 0.60, default=0.305, space='buy', load=True)
    rebelde_threshold = DecimalParameter(0.45, 0.80, default=0.554, space='buy', load=True)
    pivot_threshold   = DecimalParameter(0.50, 0.85, default=0.627, space='buy', load=True)

    # --- FIXED DEFAULTS ---
    stoploss = -0.99 
    trailing_stop = False 
    timeframe = '5m'
    inf_timeframe = '1h'
    max_open_trades = 12
    startup_candle_count: int = 288

    def leverage(self, pair: str, current_time: datetime, current_rate: float,
                 proposed_leverage: float, max_leverage: float, entry_tag: Optional[str],
                 side: str, **kwargs) -> float:
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or dataframe.empty:
            return 5.0

        last = dataframe.iloc[-1]
        mode = int(last.get('market_mode', 0))
        rps  = float(last.get('risk_pressure_score', 0.5))
        vol  = float(last.get('btc_5m_std', 0.005) or 0.005)

        if mode == 1:      base, l_min, l_max = 9.0, 3.0, 10.0
        elif mode == -1:   base, l_min, l_max = 4.0, 1.0, 5.0
        else:              base, l_min, l_max = 6.0, 2.0, 7.0

        # Cap por tipo de señal (hardening de riesgo)
        if entry_tag == 'BEAR_SHORT':
            l_max = min(l_max, 4.0)
        elif entry_tag == 'SHORT_PIVOT_REBELDE':
            l_max = min(l_max, 5.0)
        elif entry_tag == 'BULL_ATRASO':
            l_max = min(l_max, 8.0)

        vol_penalty = min(vol / 0.005, 3.0) * 2.0
        rps_penalty = rps * 8.0
        
        l_score = base - vol_penalty - rps_penalty
        lev = max(l_min, min(l_max, l_score))
        return float(min(max_leverage, lev))

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # --- INDICADORES BASE V2 ---
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=14)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        
        # Safe Defaults
        dataframe['btc_5m_rsi'] = 50
        dataframe['btc_5m_std'] = 0.001
        dataframe['btc_5m_close'] = dataframe['close']
        dataframe['macro_trend'] = True
        
        # BTC Data
        btc_df_5m = self.dp.get_pair_dataframe(pair="BTC/USDT:USDT", timeframe=self.timeframe)
        btc_df_1h = self.dp.get_pair_dataframe(pair="BTC/USDT:USDT", timeframe=self.inf_timeframe)
        
        if btc_df_5m is not None and not btc_df_5m.empty:
            dataframe['btc_5m_rsi'] = ta.RSI(btc_df_5m, timeperiod=14)
            dataframe['btc_5m_std'] = btc_df_5m['close'].pct_change().rolling(24).std()
            dataframe['btc_5m_close'] = btc_df_5m['close']

        if btc_df_1h is not None and not btc_df_1h.empty:
            btc_df_1h['ema'] = ta.EMA(btc_df_1h, timeperiod=20)
            dataframe['macro_trend'] = btc_df_1h['close'] > btc_df_1h['ema']

        # market_mode: 0: LATERAL, 1: BULL, -1: BEAR
        dataframe['market_mode'] = 0
        dataframe.loc[(dataframe['macro_trend'] == True) & (dataframe['btc_5m_rsi'] > 55), 'market_mode'] = 1
        dataframe.loc[(dataframe['macro_trend'] == False) & (dataframe['btc_5m_rsi'] < 45), 'market_mode'] = -1
        
        dataframe['atraso_real'] = dataframe['btc_5m_close'].pct_change(5) - dataframe['close'].pct_change(5)

        # --- INDICADORES ADAPTIVE V3 ---
        CORR_WINDOW = int(self.corr_window.value)
        btc_ret = dataframe['btc_5m_close'].pct_change()
        pair_ret = dataframe['close'].pct_change()

        dataframe['corr_btc'] = pair_ret.rolling(CORR_WINDOW).corr(btc_ret).fillna(0.8)
        corr_mean = dataframe['corr_btc'].rolling(CORR_WINDOW * 7).mean().fillna(0.8)
        dataframe['corr_drop'] = corr_mean - dataframe['corr_btc']
        dataframe['divergence_btc'] = btc_ret.rolling(12).mean() - pair_ret.rolling(12).mean()

        atr_pct = dataframe['atr'] / dataframe['close']
        dataframe['atr_pct'] = atr_pct
        atr_roll = atr_pct.rolling(CORR_WINDOW).rank(pct=True).fillna(0.5)
        corr_inv = (1 - dataframe['corr_btc']).clip(0, 1)
        div_abs = dataframe['divergence_btc'].abs()
        div_roll = div_abs.rolling(CORR_WINDOW).rank(pct=True).fillna(0.5)

        dataframe['risk_pressure_score'] = (
            float(self.w_corr.value) * corr_inv +
            float(self.w_div.value) * div_roll +
            float(self.w_atr.value) * atr_roll
        ).clip(0, 1)

        ema_fast = ta.EMA(dataframe, timeperiod=8)
        ema_slow = ta.EMA(dataframe, timeperiod=21)
        ema_cross_bear = (ema_fast < ema_slow).astype(float)
        btc_bear_macro = (dataframe['market_mode'] == -1).astype(float)

        dataframe['pivot_short_score'] = (
            float(self.w_rps.value) * dataframe['risk_pressure_score'] +
            float(self.w_ema.value) * ema_cross_bear +
            float(self.w_macro.value) * btc_bear_macro
        ).clip(0, 1)

        # Máquina de estados
        state = pd.Series(0, index=dataframe.index)
        state[dataframe['risk_pressure_score'] > float(self.alerta_threshold.value)] = 1
        state[(dataframe['risk_pressure_score'] > float(self.rebelde_threshold.value)) & (dataframe['corr_drop'] > 0.15)] = 2
        state[dataframe['pivot_short_score'] > float(self.pivot_threshold.value)] = 3
        
        corr_recovering = dataframe['corr_btc'] > dataframe['corr_btc'].shift(6)
        state[(state == 2) & corr_recovering & (dataframe['risk_pressure_score'] < 0.40)] = 4
        dataframe['state_pair'] = state

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dynamic_threshold = dataframe['btc_5m_std'] * float(self.btc_threshold_mult.value)

        corr_floor = dataframe['corr_btc'].rolling(96).quantile(0.30).fillna(0.55)
        atr_median = dataframe['atr_pct'].rolling(144).median().fillna(dataframe['atr_pct'])
        div_floor = dataframe['divergence_btc'].abs().rolling(96).median().fillna(dataframe['divergence_btc'].abs())
        corr_drop_floor = dataframe['corr_drop'].rolling(96).quantile(0.60).fillna(0.0)
        short_score_floor = float(self.alerta_threshold.value) + (
            float(self.rebelde_threshold.value) - float(self.alerta_threshold.value)
        ) * float(self.short_score_floor_mult.value)
        long_risk_guard = dataframe['risk_pressure_score'] < (
            float(self.alerta_threshold.value) * float(self.long_risk_guard_factor.value)
        )
        bull_quality_guard = (
            (dataframe['corr_btc'] > corr_floor) &
            (dataframe['pivot_short_score'] < float(self.pivot_threshold.value) * 0.80) &
            long_risk_guard
        )
        lateral_quality_guard = (
            (dataframe['atr_pct'] <= atr_median) &
            (dataframe['corr_btc'] > corr_floor) &
            long_risk_guard
        )
        
        # RUTAS V2
        # Crossover de atraso (evento técnico) en vez de señal constante permanente
        bull_long = (
            (dataframe['market_mode'] == 1) &
            (dataframe['atraso_real'] > dynamic_threshold) &
            (dataframe['atraso_real'].shift(1) <= dataframe['btc_5m_std'].shift(1) * float(self.btc_threshold_mult.value)) &
            bull_quality_guard
        )
        lateral_long = (
            (dataframe['market_mode'] == 0) &
            (dataframe['rsi'] < self.rsi_buy_min.value) &
            (dataframe['rsi'].shift(1) >= self.rsi_buy_min.value) &
            lateral_quality_guard
        )
        
        # RUTA V2 MEJORADA: BEAR_SHORT CON FILTROS ADAPTATIVOS
        # NADA DE TIEMPOS: El corto se activa en el momento exacto (crossover) de expansión de divergencia
        short_div_signal = dataframe['divergence_btc'] > div_floor
        short_div_cross = short_div_signal & (~short_div_signal.shift(1).fillna(False))
        bear_short = (
            (dataframe['market_mode'] == -1) &
            short_div_cross &
            (dataframe['pivot_short_score'] > short_score_floor) &
            (dataframe['risk_pressure_score'] > float(self.alerta_threshold.value)) &
            (dataframe['corr_drop'] > corr_drop_floor) &
            (dataframe['atr_pct'] > atr_median) &
            (~dataframe['state_pair'].isin([2, 4]))
        )

        # RUTA V3: SHORT PIVOT
        pivot_short = (
            (dataframe['market_mode'] <= 0) &
            (dataframe['state_pair'] == 3) &
            (dataframe['state_pair'].shift(1) != 3) & # Entra solo en la transición de estado (evento obj)
            (dataframe['pivot_short_score'] > float(self.pivot_threshold.value)) &
            (dataframe['corr_btc'] < corr_floor) &
            (dataframe['divergence_btc'] > div_floor) &
            (dataframe['corr_drop'] > corr_drop_floor)
        )

        # Aplicar Longs
        dataframe.loc[bull_long & ~dataframe['state_pair'].isin([2, 3]), 'enter_long'] = 1
        dataframe.loc[bull_long, 'enter_tag'] = 'BULL_ATRASO'
        
        dataframe.loc[lateral_long & ~dataframe['state_pair'].isin([2, 3]), 'enter_long'] = 1
        dataframe.loc[lateral_long, 'enter_tag'] = 'LATERAL_SCALP'
        
        # Aplicar Shorts
        dataframe.loc[bear_short, 'enter_short'] = 1
        dataframe.loc[bear_short, 'enter_tag'] = 'BEAR_SHORT'

        dataframe.loc[pivot_short, 'enter_short'] = 1
        dataframe.loc[pivot_short, 'enter_tag'] = 'SHORT_PIVOT_REBELDE'
        
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[(dataframe['market_mode'] <= 0) & (dataframe['rsi'] > 60), 'exit_long'] = 1
        dataframe.loc[(dataframe['market_mode'] == 1) & (dataframe['rsi'] > 80), 'exit_long'] = 1
        return dataframe

    def custom_exit(self, pair: str, trade: Trade, current_time: datetime,
                    current_rate: float, current_profit: float, **kwargs):
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or dataframe.empty: return None
        last = dataframe.iloc[-1]
        
        state = int(last.get('state_pair', 0))
        market_mode = int(last.get('market_mode', 0))
        rps = float(last.get('risk_pressure_score', 0))
        atr_pct = float((last['atr'] / last['close']) if last.get('close', 0) else 0.01)

        if not trade.is_short:
            # Contingencia Rebelde: Salida agresiva si el par se desacopla con daño
            contingency_exit = -0.05 - (rps - 0.60) * 0.175
            if state in [2, 3] and current_profit < contingency_exit:
                return f'CONTINGENCIA_REBELDE_RPS_{rps:.2f}'
        else:
            # Contingencia temporal anti-liquidación: SOLO depende del Risk Pressure Score, no de horas fijas.
            # Si el modo macro deja de ser BEAR y estamos en pérdida, salir rápido.
            if market_mode != -1 and current_profit < 0:
                return f'SHORT_MODE_INVALIDATED_RPS_{rps:.2f}'

            # Toma de ganancia orgánica en shorts para evitar reversión por sobre-rotación.
            short_tp_floor = atr_pct * (0.8 + rps)
            if current_profit > short_tp_floor:
                return f'SHORT_TP_ATR_RPS_{rps:.2f}'

            short_pain_limit = -atr_pct * (1.0 + rps)
            if rps > float(self.alerta_threshold.value) and current_profit < short_pain_limit:
                return f'STALE_SHORT_RPS_{rps:.2f}'
        
        return None

    def custom_stoploss(self, pair: str, trade: Trade, current_time: datetime,
                        current_rate: float, current_profit: float, **kwargs) -> float:
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or dataframe.empty:
            return self.stoploss
        last_candle = dataframe.iloc[-1]
        
        state = int(last_candle.get('state_pair', 0))
        mult = float(self.stoploss_atr_mult.value)
        rps = float(last_candle.get('risk_pressure_score', 0.5))
        lev = float(getattr(trade, 'leverage', 1.0) or 1.0)
        atr_pct = float((last_candle['atr'] / last_candle['close']) if last_candle['close'] else 0)
        btc_std = float(last_candle.get('btc_5m_std', atr_pct) or atr_pct)

        # Ajuste adaptativo por régimen: nunca colapsar el stop a micro-ruido.
        if last_candle['market_mode'] == -1:
            mult *= (0.95 - 0.25 * min(max(rps, 0.0), 1.0))

        if state in [2, 3]:
            mult *= (0.9 - 0.2 * min(max(rps, 0.0), 1.0))
        elif state == 1:
            mult *= (0.95 - 0.15 * min(max(rps, 0.0), 1.0))

        dynamic_stop = (last_candle['atr'] * mult) / last_candle['close']
        if pd.isna(dynamic_stop) or dynamic_stop <= 0:
            return self.stoploss

        # Piso dinámico anti-microstop basado en ruido observado (ATR + volatilidad BTC),
        # escalado por leverage para evitar cierre instantáneo en detail=1m.
        micro_noise = max(atr_pct, btc_std)
        lev_scale = np.sqrt(max(1.0, lev))
        dynamic_stop = max(
            dynamic_stop,
            micro_noise * lev_scale * (1.1 + 0.4 * min(max(rps, 0.0), 1.0))
        )

        # Protección de ganancia orgánica: lock proporcional al ATR y al profit actual.
        if current_profit > atr_pct * 2:
            trailing_gap = max(atr_pct * 0.8, current_profit * 0.35)
            return -trailing_gap
        return -dynamic_stop



    def adjust_trade_position(self, trade: Trade, current_time: datetime,
                              current_rate: float, current_profit: float,
                              min_stake: Optional[float], max_stake: float,
                              current_entry_rate: float, **kwargs) -> Optional[float]:
        dataframe, _ = self.dp.get_analyzed_dataframe(trade.pair, self.timeframe)
        if dataframe is None or dataframe.empty: return None
        last_candle = dataframe.iloc[-1]

        # Saneo anti-liquidación: deshabilitar DCA en shorts (evita promedio en contra apalancado).
        if trade.is_short:
            return None
        
        # Bloqueo DCA en estados rebeldes
        if int(last_candle.get('state_pair', 0)) in [2, 3]:
            return None

        if not self.dca_enabled or current_profit > -0.02:
            return None

        count_of_entries = trade.nr_of_successful_entries
        if count_of_entries <= self.max_dca_orders.value:
            atr_drop = (last_candle['atr'] * float(self.dca_drop_mult.value)) / last_candle['close']
            if current_profit < -atr_drop:
                return trade.stake_amount * 1.4
        
        return None
