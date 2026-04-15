# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
"""
=============================================================
 CHACAL PESCADOR V1 — CAZADOR DE PICOS EN ALTCOINS DE NICHO
=============================================================
MISIÓN:
    Capturar picos de +15-30% en Fan Tokens / Sports Tokens / Gaming Tokens
    (OG, CHZ, PSG, BAR, JUV, SANTOS, LAZIO, PORTO, ACM, GAL, ALPINE, etc.)
    que tienen catalizadores propios DESACOPLADOS de BTC.

FILOSOFÍA:
    - Timeframe base: 1m (máxima precisión en el pico)
    - Timeframe señal: 15m (confirmar estructura)
    - BTC se usa como FILTRO DE REGIME, no como motor de señal
    - La señal principal es VOLUMEN ANÓMALO + MOMENTUM PROPIO del token
    - Gestión de salida: salida rápida en pico, no hold de días

CATALIZADORES DETECTABLES:
    1. Spike de volumen > 3x la media (acumulación pre-pump)
    2. Ruptura de Bollinger Band superior (momentum confirmado)
    3. RSI del token 1m > 65 con volumen creciente (FOMO activo)
    4. BTC en régimen ESTABLE (no crash activo, filtro de pánico sistémico)

GESTIÓN DE RIESGO:
    - Trailing stop agresivo para capturar máximo del pico
    - Stop-loss fijo rápido: -3.5% (los picos se revierten igual de rápido)
    - Leverage conservador: 3x (el activo ya tiene su propio apalancamiento natural)
    - max_open_trades = 1 para capital 100% concentrado en el catch

CONFIGURACIÓN PARA BACKTEST ESTUDIO:
    Par único de estudio: OG/USDT:USDT
    Cambiar en config: "pair_whitelist": ["OG/USDT:USDT"]

VERSIÓN: 1.0 — Fase de Laboratorio / Estudio
CAPITÁN: Chacal Zero Friction
"""
import numpy as np
import pandas as pd
from pandas import DataFrame
from datetime import datetime, timedelta
from typing import Optional, Any, Dict
import talib.abstract as ta
from freqtrade.strategy import IStrategy, DecimalParameter, IntParameter
from freqtrade.persistence import Trade


class ChacalPescador_V1(IStrategy):
    """
    PESCADOR DE PICOS — Especialista en Fan Tokens y Altcoins de Nicho.
    
    Detecta el momento justo antes (o al inicio) de un pico de precio
    exógeno usando volumen anómalo y ruptura de bandas como señal.
    """
    INTERFACE_VERSION = 3
    can_short = False
    use_custom_exit = True
    use_custom_stoploss = True

    # --- Trailing stop agresivo para «surfear» el pico ---
    trailing_stop = True
    trailing_stop_positive = 0.008          # activa trailing desde +0.8%
    trailing_stop_positive_offset = 0.045   # offset: deja respirar hasta +4.5%
    trailing_only_offset_is_reached = True

    # --- Stoploss base (reemplazado por custom_stoploss en ejecución) ---
    stoploss = -0.99  # nunca se toca, custom_stoploss manda

    # Timeframes
    timeframe = '1m'       # precisión de entrada/salida
    inf_timeframe = '15m'  # estructura y confirmación

    # Capital concentrado: 1 trade a la vez durante el estudio
    max_open_trades = 1
    startup_candle_count: int = 300

    # ─────────────────────────────────────────────
    # PARÁMETROS OPTIMIZABLES (espacio de backtest)
    # ─────────────────────────────────────────────

    # Umbral de volumen anómalo (múltiplo de la media)
    vol_spike_mult = DecimalParameter(2.0, 5.0, default=3.0, space='buy', load=True)

    # RSI mínimo del token para confirmar momentum (no comprar en caída)
    rsi_momentum_min = IntParameter(50, 70, default=58, space='buy', load=True)

    # Bollinger Band: desviación estándar
    bb_std = IntParameter(2, 3, default=2, space='buy', load=True)

    # Porcentaje mínimo de ruptura sobre la BB superior
    bb_break_pct = DecimalParameter(0.001, 0.02, default=0.005, space='buy', load=True)

    # Stop-loss dinámico: múltiplo de ATR
    atr_stop_mult = DecimalParameter(1.0, 2.5, default=1.5, space='sell', load=True)

    # Exit: Take-Profit rápido si RSI cae de este umbral (pico ya pasó)
    rsi_exit_overbought = IntParameter(75, 90, default=80, space='sell', load=True)

    # Guardia de tiempo: solo operar en horas de mayor actividad
    time_guard_start = IntParameter(6, 12, default=8, space='buy', load=True)
    time_guard_end = IntParameter(18, 23, default=22, space='buy', load=True)

    # Confirmación 15m: RSI mínimo para confirmar estructura alcista
    rsi_15m_min = IntParameter(40, 60, default=48, space='buy', load=True)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Indicadores 1m del token + contexto 15m + filtro BTC.
        """
        pair = metadata['pair']

        # ── INDICADORES BASE 1m ──────────────────────────────────────
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=14)

        # Bollinger Bands dinámicas (std configurable)
        upper, mid, lower = ta.BBANDS(
            dataframe['close'],
            timeperiod=20,
            nbdevup=float(self.bb_std.value),
            nbdevdn=float(self.bb_std.value)
        )
        dataframe['bb_upper'] = upper
        dataframe['bb_mid'] = mid
        dataframe['bb_lower'] = lower
        dataframe['bb_width'] = (upper - lower) / mid  # volatilidad relativa BB

        # VOLUMEN: media vs spike
        dataframe['volume_mean_30'] = dataframe['volume'].rolling(30).mean()
        dataframe['volume_mean_60'] = dataframe['volume'].rolling(60).mean()
        dataframe['volume_ratio'] = dataframe['volume'] / dataframe['volume_mean_60'].replace(0, np.nan)

        # MOMENTUM PROPIO: aceleración de precio
        dataframe['pct_change_5'] = dataframe['close'].pct_change(5)    # retorno 5m
        dataframe['pct_change_15'] = dataframe['close'].pct_change(15)  # retorno 15m

        # MACD para confirmación de momentum
        macd, signal, hist = ta.MACD(dataframe, fastperiod=8, slowperiod=17, signalperiod=9)
        dataframe['macd'] = macd
        dataframe['macd_signal'] = signal
        dataframe['macd_hist'] = hist

        # EMA cortas para dirección
        dataframe['ema8'] = ta.EMA(dataframe, timeperiod=8)
        dataframe['ema21'] = ta.EMA(dataframe, timeperiod=21)

        # ── CONTEXTO 15m ─────────────────────────────────────────────
        df_15m = self.dp.get_pair_dataframe(pair=pair, timeframe=self.inf_timeframe).copy()

        if not df_15m.empty:
            df_15m['rsi_15m'] = ta.RSI(df_15m, timeperiod=14)
            df_15m['ema21_15m'] = ta.EMA(df_15m, timeperiod=21)
            df_15m['volume_mean_15m'] = df_15m['volume'].rolling(20).mean()
            df_15m['vol_ratio_15m'] = df_15m['volume'] / df_15m['volume_mean_15m'].replace(0, np.nan)

            # Alinear al 1m por forward-fill
            df_15m.set_index('date', inplace=True)
            aligned = df_15m[['rsi_15m', 'ema21_15m', 'vol_ratio_15m']].reindex(
                dataframe['date']
            ).ffill()
            dataframe['rsi_15m'] = aligned['rsi_15m'].values
            dataframe['ema21_15m'] = aligned['ema21_15m'].values
            dataframe['vol_ratio_15m'] = aligned['vol_ratio_15m'].values
        else:
            dataframe['rsi_15m'] = 50.0
            dataframe['ema21_15m'] = dataframe['close']
            dataframe['vol_ratio_15m'] = 1.0

        # ── FILTRO BTC (régimen sistémico) ───────────────────────────
        btc_1m = self.dp.get_pair_dataframe(pair="BTC/USDT:USDT", timeframe='1m').copy()

        if not btc_1m.empty:
            btc_1m['btc_rsi'] = ta.RSI(btc_1m, timeperiod=14)
            btc_1m['btc_pct_30'] = btc_1m['close'].pct_change(30)   # retorno 30 mins
            btc_1m['btc_pct_60'] = btc_1m['close'].pct_change(60)   # retorno 1h
            btc_1m.set_index('date', inplace=True)
            aligned_btc = btc_1m[['btc_rsi', 'btc_pct_30', 'btc_pct_60']].reindex(
                dataframe['date']
            ).ffill()
            dataframe['btc_rsi'] = aligned_btc['btc_rsi'].values
            dataframe['btc_pct_30'] = aligned_btc['btc_pct_30'].values
            dataframe['btc_pct_60'] = aligned_btc['btc_pct_60'].values
        else:
            dataframe['btc_rsi'] = 50.0
            dataframe['btc_pct_30'] = 0.0
            dataframe['btc_pct_60'] = 0.0

        # ── SCORE DE PICO: señal sintética de 0 a 3 ─────────────────
        # Composición:
        #   +1 si volumen_ratio > umbral configurado
        #   +1 si precio supera BB superior
        #   +1 si RSI en zona de momentum (no overbought extremo)
        score = pd.Series(0.0, index=dataframe.index)
        score += (dataframe['volume_ratio'] > float(self.vol_spike_mult.value)).astype(float)
        score += (dataframe['close'] > dataframe['bb_upper'] * (1 + float(self.bb_break_pct.value))).astype(float)
        score += (dataframe['rsi'].between(float(self.rsi_momentum_min.value), 82)).astype(float)
        dataframe['pico_score'] = score

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        SEÑAL DE ENTRADA: Pico detectado con triple confirmación.

        Condiciones:
          1. Volumen anómalo (> vol_spike_mult × media)               → señal principal
          2. Precio rompiendo BB superior                              → confirma dirección
          3. RSI propio en zona momentum (no en extremo overbought)   → confirma fuerza
          4. Tendencia 15m alcista (precio sobre EMA21-15m)           → contexto
          5. BTC NO en caída libre (filtro de colapso sistémico)      → seguridad
          6. Guardia horaria                                           → liquidez mínima
        """
        time_guard = (
            (dataframe['date'].dt.hour >= self.time_guard_start.value) &
            (dataframe['date'].dt.hour < self.time_guard_end.value)
        )

        # Filtro BTC: no entrar si BTC cae >3% en 30m (pánico sistémico)
        btc_safe = (
            (dataframe['btc_pct_30'] > -0.03) &
            (dataframe['btc_rsi'] > 30)  # no RSI extremo de crash
        )

        # Confirmación 15m: estructura alcista
        estructura_15m = (
            (dataframe['close'] > dataframe['ema21_15m']) &
            (dataframe['rsi_15m'] >= self.rsi_15m_min.value)
        )

        # SEÑAL PRINCIPAL: score completo (los 3 componentes)
        pico_confirmado = (dataframe['pico_score'] >= 2.5)

        # Señal de entrada compuesta
        entrada = (
            pico_confirmado &
            estructura_15m &
            btc_safe &
            time_guard &
            (dataframe['volume'] > 0)  # candle válida
        )

        dataframe.loc[entrada, 'enter_long'] = 1
        dataframe.loc[entrada, 'enter_tag'] = 'PICO_NICHO_V1'

        # Señal secundaria: pre-pump (solo 2 componentes pero con volumen extremo)
        pre_pump = (
            (dataframe['pico_score'] >= 1.5) &
            (dataframe['volume_ratio'] > float(self.vol_spike_mult.value) * 1.5) &  # volumen muy anómalo
            estructura_15m &
            btc_safe &
            time_guard
        )
        dataframe.loc[pre_pump & ~entrada, 'enter_long'] = 1
        dataframe.loc[pre_pump & ~entrada, 'enter_tag'] = 'PRE_PUMP_VOLUMEN'

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Salida base (el trailing stop y custom_exit hacen el trabajo real).
        Señal de salida básica: RSI extremo overbought = el pico ya pasó.
        """
        dataframe.loc[
            (dataframe['rsi'] > self.rsi_exit_overbought.value) &
            (dataframe['macd_hist'] < 0),  # confirmación: MACD bajando
            'exit_long'
        ] = 1
        return dataframe

    def custom_stoploss(self, pair: str, trade: Trade, current_time: datetime,
                        current_rate: float, current_profit: float, **kwargs) -> float:
        """
        Stop-loss dinámico basado en ATR del token.
        En picos, el ATR 1m puede ser muy alto → stop más amplio para no ser barrido.
        Máximo riesgo: -5% del trade.
        """
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or dataframe.empty:
            return -0.035

        last = dataframe.iloc[-1]
        atr_stop = (last['atr'] * float(self.atr_stop_mult.value)) / current_rate

        # Cap: nunca arriesgar más de 5% ni menos de 1.5%
        return -max(0.015, min(0.05, atr_stop))

    def custom_exit(self, pair: str, trade: Trade, current_time: datetime,
                    current_rate: float, current_profit: float, **kwargs) -> Optional[str]:
        """
        Lógica de salida inteligente para picos:
        
        1. PICO_EXPIRADO: Si llevamos más de 4h sin superar +5% → salir (el pico no llegó)
        2. REVERSAL_RAPIDO: Si caímos >2% desde el máximo del trade → salir rápido
        3. PROFIT_LOCK: Si tenemos +8% y el RSI empieza a colapsar → asegurar
        """
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or dataframe.empty:
            return None

        last = dataframe.iloc[-1]
        trade_duration = (current_time - trade.open_date_utc).total_seconds() / 60  # en minutos

        # 1. PICO EXPIRADO: 4 horas sin llegar al +5% mínimo esperado
        if trade_duration > 240 and current_profit < 0.05:
            return 'PICO_EXPIRADO_4H'

        # 2. PICO MÁXIMO CONFIRMADO: RSI extremo + MACD bajando → ya pasó el pico
        if (current_profit > 0.08 and
                last['rsi'] > self.rsi_exit_overbought.value and
                last['macd_hist'] < 0):
            return 'PICO_MAXIMO_ALCANZADO'

        # 3. PROTECCIÓN RÁPIDA: trade muy nuevo y ya cayendo fuerte con volumen
        if (trade_duration < 30 and
                current_profit < -0.025 and
                last['volume_ratio'] > float(self.vol_spike_mult.value)):
            # Volumen alto bajando en los primeros 30m = pico fue en contra
            return 'FALSO_PICO_SALIDA_RAPIDA'

        # 4. TIME-DECAY: no quedarse atrapado más de 24h en un token de nicho
        if trade_duration > 1440 and current_profit < 0.03:
            return 'ZOMBIE_24H_KILL'

        return None

    def leverage(self, pair: str, current_time: datetime, current_rate: float,
                 proposed_leverage: float, max_leverage: float, side: str, **kwargs) -> float:
        """
        Leverage CONSERVADOR para tokens de nicho.
        El token ya tiene su propio apalancamiento natural (mueve 20-30%).
        No necesitamos leverage alto; necesitamos sobrevivir el spread y la volatilidad.
        
        3x estándar → menor riesgo de liquidación en picos falsos.
        """
        return min(3.0, max_leverage)

    def adjust_trade_position(self, trade: Trade, current_time: datetime,
                               current_rate: float, current_profit: float,
                               min_stake: Optional[float], max_stake: float,
                               **kwargs) -> Optional[float]:
        """
        NO usamos DCA agresivo en tokens de nicho.
        Solo un pequeño refuerzo si estamos en pre-pump confirmado y perdemos <2%.
        """
        if (current_profit < -0.015 and
                current_profit > -0.04 and
                trade.nr_of_successful_entries < 2):
            # Refuerzo pequeño: 50% del stake original
            return trade.stake_amount * 0.5
        return None
