# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          CHACAL TRIPLE MODE — v1.0 — ARQUITECTURA INSTITUCIONAL            ║
║                                                                              ║
║  Tres modos de operación SHORT según régimen de mercado BTC:                ║
║                                                                              ║
║  [3] SUPER BEAR  → BTC RSI1h < super_bear_rsi   | Agresivo, deja correr    ║
║  [2] BEAR NORMAL → BTC RSI1h < bear_rsi         | Estándar, ADN Época 46   ║
║  [1] LATERAL BEAR→ BTC < EMA50 pero RSI alto    | Quirúrgico, sale rápido  ║
║  [0] FUERA       → BTC > EMA50                  | No operamos              ║
║                                                                              ║
║  TODOS los umbrales de régimen + parámetros de entrada/salida son           ║
║  HYPEROPTIMIZABLES. El algoritmo encontrará las fronteras óptimas.          ║
║                                                                              ║
║  ADN Época 46 (v_factor, pulse, roi, sl por par) como DEFAULT de partida.  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
import pandas as pd
import os
from pandas import DataFrame
from datetime import datetime, timezone
from typing import Optional, Union, Any
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.strategy import DecimalParameter, IStrategy, IntParameter
from freqtrade.persistence import Trade


class ChacalTripleMode(IStrategy):
    INTERFACE_VERSION = 3
    can_short: bool = True
    use_custom_exit = True
    use_custom_stoploss = True

    # =========================================================================
    # ADN POR PAR — Época 46 calibrado (SL de ADA y BNB corregidos)
    # =========================================================================
    hyperopt_dna = {
        "BTC/USDT:USDT":  {"v_factor": 4.660, "pulse_change": 0.004, "bear_roi": 0.022, "bear_sl": -0.031},
        "ETH/USDT:USDT":  {"v_factor": 5.769, "pulse_change": 0.004, "bear_roi": 0.018, "bear_sl": -0.031},
        "SOL/USDT:USDT":  {"v_factor": 5.386, "pulse_change": 0.001, "bear_roi": 0.042, "bear_sl": -0.040},
        "BNB/USDT:USDT":  {"v_factor": 3.378, "pulse_change": 0.003, "bear_roi": 0.011, "bear_sl": -0.060},  # fix: era -0.048
        "XRP/USDT:USDT":  {"v_factor": 5.133, "pulse_change": 0.004, "bear_roi": 0.042, "bear_sl": -0.054},
        "ADA/USDT:USDT":  {"v_factor": 3.408, "pulse_change": 0.005, "bear_roi": 0.042, "bear_sl": -0.055},  # fix: era -0.022
        "AVAX/USDT:USDT": {"v_factor": 5.692, "pulse_change": 0.005, "bear_roi": 0.010, "bear_sl": -0.053},
        "LINK/USDT:USDT": {"v_factor": 5.671, "pulse_change": 0.005, "bear_roi": 0.038, "bear_sl": -0.041},
    }

    # =========================================================================
    # PARÁMETROS MAESTROS — SELECTOR DE RÉGIMEN (ADN DE ORO 789%)
    # =========================================================================
    
    # Umbrales optimizados para Agosto 2024
    super_bear_rsi = IntParameter(20, 35, default=20, space='buy', optimize=False)
    bear_rsi       = IntParameter(35, 55, default=40, space='buy', optimize=False)

    # =========================================================================
    # PARÁMETROS DE ENTRADA — MODO BEAR & SUPER BEAR (DNA 1.44)
    # =========================================================================
    sb_v_factor    = DecimalParameter(1.2, 2.0, default=1.44,  space='buy', optimize=False)
    sb_rsi_entry   = IntParameter(25, 45,       default=32,   space='buy', optimize=False)
    sb_fractal_min = DecimalParameter(0.10, 0.45, default=0.25, space='buy', optimize=False)

    # Modo Bear Normal
    bear_v_factor    = DecimalParameter(1.2, 2.0, default=1.44, space='buy', optimize=False)
    bear_rsi_entry   = IntParameter(25, 45,       default=32,   space='buy', optimize=False)
    bear_fractal_min = DecimalParameter(0.25, 0.55, default=0.35, space='buy', optimize=False)
    
    # ADX Base threshold para override de riesgo en fuertes pánicos
    adx_threshold = IntParameter(20, 35, default=26, space='buy', optimize=False)

    # =========================================================================
    # PARÁMETROS DE ENTRADA — MODO LATERAL BEAR [1] (DNA 30%)
    # =========================================================================
    lat_v_factor    = DecimalParameter(2.0, 6.0, default=2.8,  space='buy', optimize=False)
    lat_rsi_entry   = IntParameter(15, 30,        default=25,   space='buy', optimize=False)
    lat_fractal_min = DecimalParameter(0.45, 0.75, default=0.55, space='buy', optimize=False)

    # Umbral de riesgo fractal — Permisivo (0.88) para no bloquear el profit de Bear44
    fractal_risk_threshold = DecimalParameter(0.50, 0.95, default=0.88, space='buy', optimize=False)

    # =========================================================================
    # PARÁMETROS DE SALIDA POR MODO (ROI DINÁMICO SIMULADO)
    # =========================================================================
    sb_rebound_thresh   = DecimalParameter(0.015, 0.035, default=0.024, space='sell', optimize=False)
    bear_rebound_thresh = DecimalParameter(0.010, 0.025, default=0.018, space='sell', optimize=False)
    lat_rebound_thresh  = DecimalParameter(0.008, 0.018, default=0.012, space='sell', optimize=False)

    # =========================================================================
    # CONFIGURACIÓN FIJA (no hyperopt — son controles de seguridad)
    # =========================================================================
    roi_base   = 0.045     # Sincronizado con Bear44 (0.045)
    bear_stoploss = -0.090 # Sincronizado con Bear44 (-0.09)
    stoploss   = -0.150    # SL Freqtrade (safety net global)

    trailing_stop                   = False
    trailing_stop_positive          = 0.015
    trailing_stop_positive_offset   = 0.038 # Dejamos este margen como en Bear44
    trailing_only_offset_is_reached = True

    timeframe        = '5m'
    max_open_trades  = 8

    minimal_roi = {
        "0": 0.045
    }

    # =========================================================================
    # PARES INFORMATIVOS — Vital para el Selector de Régimen
    # =========================================================================
    def informative_pairs(self):
        """
        Define los pares adicionales que el bot debe cargar (BTC y el par actual en 1h)
        """
        pairs = self.dp.current_whitelist()
        informative_pairs = [(p, '1h') for p in pairs]
        informative_pairs.append(("BTC/USDT:USDT", "1h"))
        return informative_pairs

    # Anti-zombie: tiempos máximos por trade
    max_trade_duration_hours = 24
    max_loss_duration_hours  = 12

    # Auditoría selector:
    # AUTO (default) | SUPER | BEAR | LATERAL
    FORCE_MODE = os.getenv("CHACAL_FORCE_MODE", "AUTO").strip().upper()

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _sl_for_pair(self, pair: str) -> float:
        dna = self.hyperopt_dna.get(pair, {"bear_sl": self.bear_stoploss})
        return dna.get("bear_sl", self.bear_stoploss)

    def _roi_for_pair(self, pair: str) -> float:
        dna_roi = self.hyperopt_dna.get(pair, {"bear_roi": 0.03})["bear_roi"]
        return max(self.roi_base, dna_roi * 0.8)

    def _safe_series(self, dataframe: DataFrame, column: str, default) -> pd.Series:
        if column not in dataframe.columns:
            dataframe[column] = default
        return dataframe[column].fillna(default if not callable(default) else default)

    def _clamp(self, value: float, low: float = 0.0, high: float = 1.0) -> float:
        return max(low, min(high, float(value)))

    def _resolve_forced_regime(self) -> Optional[int]:
        mapping = {
            "SUPER": 3,
            "BEAR": 2,
            "LATERAL": 1,
            "AUTO": None,
            "": None,
        }
        return mapping.get(self.FORCE_MODE, None)

    def informative_pairs(self):
        pairs = self.dp.current_whitelist()
        informative_pairs  = [(pair, '1m') for pair in pairs]     # Kill switch fino
        informative_pairs += [(pair, '1h') for pair in pairs]     # Macro par
        informative_pairs += [("BTC/USDT:USDT", "1h")]            # Régimen macro
        return informative_pairs

    def leverage(self, pair: str, current_time: datetime, current_rate: float,
                 proposed_leverage: float, max_leverage: float, side: str, **kwargs) -> float:
        return 5.0

    # =========================================================================
    # INDICADORES — incluye detección de régimen
    # =========================================================================

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dna = self.hyperopt_dna.get(metadata['pair'], self.hyperopt_dna["BTC/USDT:USDT"])

        # --- TIMEFRAME PRINCIPAL 5m ---
        dataframe['atr']         = ta.ATR(dataframe, timeperiod=14)
        dataframe['adx']         = ta.ADX(dataframe, timeperiod=14)
        dataframe['rsi']         = ta.RSI(dataframe, timeperiod=14)
        dataframe['volume_mean'] = dataframe['volume'].rolling(20).mean()
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lowerband'] = bollinger['lower']
        dataframe['bb_middleband'] = bollinger['mid']

        dataframe['price_change']      = dataframe['close'].pct_change()
        dataframe['atr_pct_5m']        = (dataframe['atr'] / dataframe['close']).replace([np.inf, -np.inf], np.nan).fillna(0.004)
        dataframe['vol_rank_5m']       = dataframe['atr_pct_5m'].rolling(72).rank(pct=True).fillna(0.5)
        dataframe['price_change_abs']  = dataframe['price_change'].abs().fillna(0.0)

        # --- TIMEFRAME 1M (kill switch fino) ---
        info_1m = self.dp.get_pair_dataframe(pair=metadata['pair'], timeframe="1m")
        if not info_1m.empty:
            info_1m['rsi_1m']          = ta.RSI(info_1m, timeperiod=14)
            info_1m['price_change_1m'] = (info_1m['close'] - info_1m['open']) / info_1m['open']
            info_1m['shock_1m']        = info_1m['price_change_1m'].abs().rolling(5).max()
            info_1m = info_1m[['date', 'rsi_1m', 'price_change_1m', 'shock_1m']]
            dataframe = pd.merge(dataframe, info_1m, on='date', how='left').ffill()

        dataframe['rsi_1m']          = self._safe_series(dataframe, 'rsi_1m', 50.0)
        dataframe['price_change_1m'] = self._safe_series(dataframe, 'price_change_1m', 0.0)
        dataframe['shock_1m']        = self._safe_series(dataframe, 'shock_1m', 0.0)

        # --- TIMEFRAME 1H PAR (contexto de tendencia del par) ---
        pair_1h = self.dp.get_pair_dataframe(pair=metadata['pair'], timeframe="1h")
        if pair_1h is not None and not pair_1h.empty:
            pair_1h['atr_1h']       = ta.ATR(pair_1h, timeperiod=14)
            pair_1h['atr_pct_1h']   = (pair_1h['atr_1h'] / pair_1h['close']).replace([np.inf, -np.inf], np.nan)
            pair_1h['ema21_1h']     = ta.EMA(pair_1h, timeperiod=21)
            pair_1h['dist_ema21']   = ((pair_1h['ema21_1h'] - pair_1h['close']) / pair_1h['close']).replace([np.inf, -np.inf], np.nan)
            pair_1h = pair_1h[['date', 'atr_pct_1h', 'dist_ema21']]
            dataframe = pd.merge(dataframe, pair_1h, on='date', how='left').ffill()

        dataframe['atr_pct_1h'] = self._safe_series(dataframe, 'atr_pct_1h', dataframe['atr_pct_5m'].rolling(12).mean().fillna(0.006))
        dataframe['dist_ema21'] = self._safe_series(dataframe, 'dist_ema21', 0.0)

        # --- BTC MACRO 1H (MASTER BEAR SWITCH + RÉGIMEN) ---
        btc_1h = self.dp.get_pair_dataframe(pair="BTC/USDT:USDT", timeframe="1h")
        if not btc_1h.empty:
            btc_1h['ema50']           = ta.EMA(btc_1h, timeperiod=50)
            btc_1h['rsi_btc_1h']      = ta.RSI(btc_1h, timeperiod=14)
            btc_1h['atr_btc']         = ta.ATR(btc_1h, timeperiod=14)
            btc_1h['atr_btc_mean']    = btc_1h['atr_btc'].rolling(8).mean()
            btc_1h['btc_atr_pct_1h']  = (btc_1h['atr_btc'] / btc_1h['close']).replace([np.inf, -np.inf], np.nan)
            btc_1h['btc_dist_ema50']  = ((btc_1h['ema50'] - btc_1h['close']) / btc_1h['close']).replace([np.inf, -np.inf], np.nan)

            df_btc = btc_1h[['date', 'close', 'ema50', 'rsi_btc_1h', 'atr_btc', 'atr_btc_mean', 'btc_atr_pct_1h', 'btc_dist_ema50']].copy()
            df_btc = df_btc.rename(columns={'close': 'btc_close', 'ema50': 'btc_ema50'})
            dataframe = pd.merge(dataframe, df_btc, on='date', how='left').ffill()

            # MASTER BEAR SWITCH — idéntico a Bear44:
            # BTC bajo EMA50 + volatilidad activa (ATR > su propia media)
            btc_under_ema50 = dataframe['btc_close'] < dataframe['btc_ema50']
            btc_vol_activa  = dataframe['atr_btc'] > dataframe['atr_btc_mean']
            dataframe['master_bear_switch'] = (btc_under_ema50 & btc_vol_activa).astype(int)
        else:
            dataframe['master_bear_switch'] = 1  # FAIL-SAFE Bear44: si no hay datos BTC, operamos igual

        dataframe['btc_rsi_1h']      = self._safe_series(dataframe, 'rsi_btc_1h', 50.0)
        dataframe['btc_atr_pct_1h']  = self._safe_series(dataframe, 'btc_atr_pct_1h', 0.008)
        dataframe['btc_dist_ema50']  = self._safe_series(dataframe, 'btc_dist_ema50', 0.0)

        # FRPS (Fractal Risk Pressure Score) — Sincronizado con fórmula Bear44 (H-L)/O
        f_range = (dataframe['high'] - dataframe['low']) / dataframe['open']
        dataframe['fractal_risk_pressure'] = f_range.rolling(120).rank(pct=True).fillna(0.5)
        pulse_change = float(dna.get("pulse_change", 0.001))
        pulse_floor = max(pulse_change, 1e-6)
        dataframe['fractal_bear_quality'] = (
            (dataframe['price_change_abs'] / pulse_floor)
            .replace([np.inf, -np.inf], np.nan)
            .rolling(24)
            .mean()
            .rank(pct=True)
            .fillna(0.5)
        )

        # =====================================================================
        # DETECTOR DE RÉGIMEN — LA CLAVE DE TODA LA ARQUITECTURA
        # Lee los umbrales hyperoptimizables y clasifica cada vela en un modo
        # =====================================================================
        sb_thresh   = self.super_bear_rsi.value   # ej: 25 → por debajo = SUPER BEAR
        bear_thresh = self.bear_rsi.value          # ej: 40 → por debajo = BEAR NORMAL

        bear_active = dataframe['master_bear_switch'] == 1
        btc_rsi     = dataframe['btc_rsi_1h']

        dataframe['market_regime'] = 0  # [0] Fuera: BTC alcista o sin fuerza → NO operamos

        # [1] LATERAL BEAR: Master Switch activo pero RSI >= bear_thresh (mercado ambiguo)
        dataframe.loc[
            bear_active & (btc_rsi >= bear_thresh),
            'market_regime'
        ] = 1

        # [2] BEAR NORMAL: RSI entre super_bear_rsi y bear_rsi (tendencia bajista sostenida)
        dataframe.loc[
            bear_active & (btc_rsi < bear_thresh) & (btc_rsi >= sb_thresh),
            'market_regime'
        ] = 2

        # [3] SUPER BEAR: RSI < super_bear_rsi — pánico total, máxima agresividad
        dataframe.loc[
            bear_active & (btc_rsi < sb_thresh),
            'market_regime'
        ] = 3

        forced_regime = self._resolve_forced_regime()
        if forced_regime is None:
            dataframe['regime_source'] = 'AUTO'
        else:
            dataframe['market_regime'] = forced_regime
            dataframe['regime_source'] = f'FORCED_{self.FORCE_MODE}'

        return dataframe

    # =========================================================================
    # ENTRADAS — LÓGICA DIVERGENTE POR MODO
    # Cada modo tiene sus propios umbrales de v_factor, RSI y fractal quality
    # =========================================================================

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        pair = metadata['pair']
        dna = self.hyperopt_dna.get(pair, self.hyperopt_dna["BTC/USDT:USDT"])
        pulse = float(dna.get("pulse_change", 0.001))

        # Condición base: Pulso de caída y bajo la media (Fiel a Bear44)
        base = (
            (dataframe['price_change'] < -pulse) &
            (dataframe['close'] < dataframe['bb_middleband']) &
            (dataframe['rsi'] < 45)
        )

        # --- [3] SUPER BEAR: Agresivo, entra antes que la manada ---
        # v_factor bajo: el volumen extremo llega antes del pico de pánico
        # RSI más permisivo: ya hay inercia bajista fuerte
        # Fractal quality mínima: menor exigencia porque la caída es obvia
        super_bear_entry = (
            base &
            (dataframe['market_regime'] == 3) &
            (dataframe['volume'] > dataframe['volume_mean'] * self.sb_v_factor.value) &
            (dataframe['rsi'] < self.sb_rsi_entry.value) &
            (dataframe['fractal_bear_quality'] >= self.sb_fractal_min.value)
        )

        # --- [2] BEAR NORMAL: Estándar, ADN Época 46 como punto de partida ---
        # Mayor exigencia de volumen que Super Bear (tendencia más tranquila)
        # RSI más estricto: la tendencia es bajista pero no pánico
        bear_normal_entry = (
            base &
            (dataframe['market_regime'] == 2) &
            (dataframe['volume'] > dataframe['volume_mean'] * self.bear_v_factor.value) &
            (dataframe['rsi'] < self.bear_rsi_entry.value) &
            (dataframe['fractal_bear_quality'] >= self.bear_fractal_min.value) &
            (dataframe['adx'] > self.adx_threshold.value)
        )

        # --- [1] LATERAL BEAR: Quirúrgico, máxima exigencia ---
        # v_factor muy alto: solo entra si hay convicción de movimiento real
        # RSI muy bajo: mercado tiene que estar sobrevendido fuerte
        # Fractal quality alta: sin calidad institucional no hay entrada
        # Restricción de FRPS extra: 80% del umbral global → más conservador
        lateral_bear_entry = (
            base &
            (dataframe['market_regime'] == 1) &
            (dataframe['volume'] > dataframe['volume_mean'] * self.lat_v_factor.value) &
            (dataframe['rsi'] < self.lat_rsi_entry.value) &
            (dataframe['fractal_bear_quality'] >= self.lat_fractal_min.value) &
            (dataframe['fractal_risk_pressure'] < self.fractal_risk_threshold.value * 0.80)
        )

        # Aplicar señales (prioridad: Super Bear > Bear Normal > Lateral)
        force_suffix = ''
        forced = self._resolve_forced_regime()
        if forced is not None:
            force_suffix = f'|FORCED_{self.FORCE_MODE}'

        dataframe.loc[lateral_bear_entry, 'enter_short'] = 1
        dataframe.loc[lateral_bear_entry, 'enter_tag'] = f'LATERAL_BEAR{force_suffix}'

        dataframe.loc[bear_normal_entry, 'enter_short'] = 1
        dataframe.loc[bear_normal_entry, 'enter_tag'] = f'BEAR_NORMAL{force_suffix}'

        dataframe.loc[super_bear_entry, 'enter_short'] = 1
        dataframe.loc[super_bear_entry, 'enter_tag'] = f'SUPER_BEAR{force_suffix}'

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe  # Todo el manejo de salidas via custom_exit

    # =========================================================================
    # STOPLOSS DINÁMICO — Varía por régimen actual (no por régimen de entrada)
    # El regime actual dicta el espacio que le damos al trade
    # =========================================================================

    def custom_stoploss(self, pair: str, trade: 'Trade', current_time: datetime,
                        current_rate: float, current_profit: float, after_fill: bool, **kwargs) -> float:

        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        base_sl = abs(self._sl_for_pair(pair))

        if dataframe is None or dataframe.empty:
            return -base_sl

        last_candle = dataframe.iloc[-1]
        regime  = int(last_candle.get('market_regime', 2))
        atr_5m  = float(last_candle.get('atr_pct_5m', 0.004) or 0.004)
        atr_1h  = float(last_candle.get('atr_pct_1h', atr_5m) or atr_5m)
        frps    = self._clamp(float(last_candle.get('fractal_risk_pressure', 0.5)))
        lev     = float(getattr(trade, 'leverage', 5.0) or 5.0)

        # SL base por modo:
        # - Super Bear: más holgura (movimientos explosivos necesitan espacio)
        # - Lateral Bear: más ajustado (no queremos quemar capital en fakeouts)
        sl_mult = {3: 1.15, 2: 1.00, 1: 0.80}.get(regime, 1.00)
        base_sl = base_sl * sl_mult

        dynamic_floor = max(
            base_sl * (0.70 - 0.20 * frps),
            atr_5m * 2.2,
            atr_1h * 1.15
        )
        leverage_noise = max(1.0, np.sqrt(lev))
        dynamic_floor *= (0.95 + 0.10 * leverage_noise)

        # Si ya tenemos profit, trailing fino
        if current_profit > atr_5m * 2.2:
            trail_gap = max(atr_5m * 1.4, current_profit * (0.28 + 0.12 * frps))
            return -trail_gap

        return -max(dynamic_floor, base_sl * 0.55)

    # =========================================================================
    # SALIDA PERSONALIZADA — Adaptada al régimen ACTUAL (no al de entrada)
    # Cada modo tiene su propia tolerancia a rebotes y sus propios ROI targets
    # =========================================================================

    def custom_exit(self, pair: str, trade: 'Trade', current_time: datetime,
                    current_rate: float, current_profit: float, **kwargs):

        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or len(dataframe) == 0:
            return None

        last_candle = dataframe.iloc[-1]
        frps         = self._clamp(float(last_candle.get('fractal_risk_pressure', 0.5)))
        bear_quality = self._clamp(float(last_candle.get('fractal_bear_quality', 0.5)))
        regime       = int(last_candle.get('market_regime', 2))
        btc_rsi_1h   = float(last_candle.get('btc_rsi_1h', 50.0))
        rsi_1m       = float(last_candle.get('rsi_1m', 50.0))
        rebound_1m   = float(max(last_candle.get('price_change_1m', 0.0), 0.0))
        shock_1m     = float(last_candle.get('shock_1m', 0.0) or 0.0)

        # ----- ROI TARGET por régimen -----
        dna_roi = self._roi_for_pair(pair)
        # Super Bear: deja correr (caídas grandes en pánico)
        # Lateral Bear: sale antes (riesgo de reversión alto)
        roi_mult = {3: 1.20, 2: 1.00, 1: 0.70}.get(regime, 1.00)
        roi_target = max(
            self.roi_base * roi_mult,
            dna_roi * roi_mult
        ) * (1.0 - 0.30 * frps + 0.10 * bear_quality)
        roi_target = max(0.008, roi_target)

        if current_profit >= roi_target:
            return f"roi_mode{regime}_fp{int(frps * 100)}"

        # ----- KILL SWITCH 1M por régimen -----
        # Umbrales de rebote → más tolerante en Super Bear, más estricto en Lateral
        if regime == 3:   # SUPER BEAR: aguanta más el rebote
            rebound_thresh = self.sb_rebound_thresh.value * (1.40 - 0.30 * frps)
            rsi_exit_1m = 85 - int(frps * 5)
        elif regime == 2:  # BEAR NORMAL: comportamiento estándar
            rebound_thresh = self.bear_rebound_thresh.value * (1.10 - 0.20 * frps)
            rsi_exit_1m = 78 - int(frps * 5)
        else:              # LATERAL BEAR: sale al menor signo de reversión
            rebound_thresh = self.lat_rebound_thresh.value * max(0.60, 1.0 - 0.40 * frps)
            rsi_exit_1m = 68 - int(frps * 10)

        if rsi_1m > rsi_exit_1m:
            return f"rsi_1m_kill_m{regime}"

        if rebound_1m > rebound_thresh:
            return f"rebound_kill_m{regime}"

        if shock_1m > rebound_thresh * 1.50 and current_profit < 0.01:
            return f"shock_exit_m{regime}"

        # ----- INVALIDACIÓN MACRO -----
        # En Lateral Bear: si BTC empieza a recuperar, salimos sin preguntar
        if regime == 1 and btc_rsi_1h > 48 and current_profit < 0:
            return "lateral_macro_invalid"

        # En Bear Normal: si BTC escala demasiado, cortamos pérdidas
        if regime == 2 and btc_rsi_1h > 44 and current_profit < -0.02:
            return f"bear_macro_exit_{int(btc_rsi_1h)}"

        # ----- ANTI-ZOMBIE (tiempo máximo por trade) -----
        duration_h = (current_time - trade.open_date_utc).total_seconds() / 3600
        # Lateral Bear: timeouts más agresivos (no queremos capital atrapado)
        timeout_mult = {3: 1.20, 2: 1.00, 1: 0.75}.get(regime, 1.00)
        loss_timeout  = max(6.0,  self.max_loss_duration_hours  * (1.20 - 0.70 * frps) * timeout_mult)
        trade_timeout = max(12.0, self.max_trade_duration_hours * (1.10 - 0.40 * frps) * timeout_mult)

        if duration_h > loss_timeout and current_profit < 0:
            return f"timeout_loss_m{regime}"

        if duration_h > trade_timeout:
            return f"timeout_max_m{regime}"

        return None
