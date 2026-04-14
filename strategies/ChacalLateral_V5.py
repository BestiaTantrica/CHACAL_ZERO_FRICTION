# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
import numpy as np
import pandas as pd
from pandas import DataFrame
from datetime import datetime
import talib.abstract as ta
from freqtrade.strategy import IStrategy, DecimalParameter, IntParameter
from freqtrade.persistence import Trade

class ChacalLateral_V5(IStrategy):
    """
    CHACAL LATERAL V5 - ARQUITECTURA CUÁNTICA NATIVA 1m
    Alineado con el laboratorio "FrankenData" (Selección Sintética).
    Mejoras:
    1. Scoring Cuántico Ponderado.
    2. Zero Lookahead Bias (Nativo 1m).
    3. Profit Slider (Target Dinámico según fuerza RSI).
    4. Spread/Liquidez micro (Orderbook Proxy).
    """
    INTERFACE_VERSION = 3
    can_short = True
    use_custom_exit = True
    use_custom_stoploss = False
    
    # --- BLOQUEO TOTAL DE TRAILING STOP ---
    trailing_stop = False 
    trailing_stop_positive = None
    trailing_stop_positive_offset = 0.0
    trailing_only_offset_is_reached = False

    # --- DNA MACRO (Escalado a 1m) ---
    band_proximity    = DecimalParameter(0.0005, 0.005, default=0.002, space='buy', optimize=True)
    bb_width_max      = DecimalParameter(0.02, 0.15, default=0.08, space='buy', optimize=True)
    bb_width_min      = DecimalParameter(0.001, 0.02, default=0.005, space='buy', optimize=True)
    
    # Filtro de microestructura (Orderbook proxy)
    spread_max_limit  = DecimalParameter(0.001, 0.005, default=0.003, space='buy', optimize=True)

    # --- SCORING CUÁNTICO PONDERADO (Escala x10) ---
    # pa_bullish = 5, exhaust = 20, div = 15. Máx = 40.
    score_threshold_long  = IntParameter(5, 30, default=20, space='buy', optimize=True)
    score_threshold_short = IntParameter(5, 30, default=20, space='sell', optimize=True)
    
    # Filtros extra
    rsi_core_long_max  = IntParameter(20, 40, default=30, space='buy', optimize=True)
    rsi_core_short_min = IntParameter(40, 80, default=70, space='sell', optimize=True)

    stoploss = -0.05 
    timeframe = '1m' # NATIVO 1M
    minimal_roi = {"0": 100} 
    max_open_trades = 8

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # 1. MACRO 5m (Escalado matemáticamente a 1m multiplicando periodos por 5)
        # BB 20 en 5m = BB 100 en 1m
        bollinger = ta.BBANDS(dataframe, timeperiod=100, nbdevup=2.0, nbdevdn=2.0)
        dataframe['bb_upper'], dataframe['bb_mid'], dataframe['bb_lower'] = bollinger['upperband'], bollinger['middleband'], bollinger['lowerband']
        dataframe['bb_width'] = (dataframe['bb_upper'] - dataframe['bb_lower']) / dataframe['bb_mid']
        
        # Core RSI (14 en 5m = 70 en 1m)
        dataframe['rsi_core'] = ta.RSI(dataframe, timeperiod=70)

        # 2. MICROESTRUCTURA Y LIQUIDEZ (Orderbook proxy)
        dataframe['spread'] = (dataframe['high'] - dataframe['low']) / dataframe['close']
        
        # 3. MIRA INSTITUCIONAL (Micro 1m Nativo)
        dataframe['rsi_1m'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['ema_slow_1m'] = ta.EMA(dataframe, timeperiod=50)
        dataframe['vol_mean_1m'] = dataframe['volume'].rolling(10).mean()
        
        # --- COMPONENTES DEL SCORING CUÁNTICO ---
        # 1. Price Action Confirmation (Peso: 5)
        dataframe['pa_bullish'] = ((dataframe['close'] > dataframe['open']).astype(int)) * 5
        dataframe['pa_bearish'] = ((dataframe['close'] < dataframe['open']).astype(int)) * 5
        
        # 2. Agotamiento Micro (Peso: 20)
        dataframe['exhaust_long'] = ((dataframe['rsi_1m'] < 30).astype(int)) * 20
        dataframe['exhaust_short'] = ((dataframe['rsi_1m'] > 70).astype(int)) * 20
        
        # 3. Divergencia Simple (Peso: 15)
        dataframe['div_bullish'] = (((dataframe['close'] <= dataframe['close'].shift(1)) & (dataframe['rsi_1m'] > dataframe['rsi_1m'].shift(1))).astype(int)) * 15
        dataframe['div_bearish'] = (((dataframe['close'] >= dataframe['close'].shift(1)) & (dataframe['rsi_1m'] < dataframe['rsi_1m'].shift(1))).astype(int)) * 15
        
        # Construcción del SCORING
        dataframe['score_long'] = dataframe['pa_bullish'] + dataframe['exhaust_long'] + dataframe['div_bullish']
        dataframe['score_short'] = dataframe['pa_bearish'] + dataframe['exhaust_short'] + dataframe['div_bearish']
        
        # 4. Airbag Persistencia (3 velas por debajo de EMA con volumen)
        dataframe['airbag_long_trigger'] = ((dataframe['close'] < dataframe['ema_slow_1m']) & (dataframe['volume'] > dataframe['vol_mean_1m'])).rolling(3).min()
        dataframe['airbag_short_trigger'] = ((dataframe['close'] > dataframe['ema_slow_1m']) & (dataframe['volume'] > dataframe['vol_mean_1m'])).rolling(3).min()
        
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # GATILLO CUÁNTICO
        long_cond = (
            (dataframe['bb_width'] < self.bb_width_max.value) & 
            (dataframe['bb_width'] > self.bb_width_min.value) & 
            (dataframe['spread'] < self.spread_max_limit.value) & # Filtro liquidez
            (dataframe['close'] <= dataframe['bb_lower'] * (1 + self.band_proximity.value)) & 
            (dataframe['rsi_core'] < self.rsi_core_long_max.value) &
            (dataframe['score_long'] >= self.score_threshold_long.value)
        )
        
        short_cond = (
            (dataframe['bb_width'] < self.bb_width_max.value) & 
            (dataframe['bb_width'] > self.bb_width_min.value) & 
            (dataframe['spread'] < self.spread_max_limit.value) & # Filtro liquidez
            (dataframe['close'] >= dataframe['bb_upper'] * (1 - self.band_proximity.value)) & 
            (dataframe['rsi_core'] > self.rsi_core_short_min.value) &
            (dataframe['score_short'] >= self.score_threshold_short.value)
        )

        dataframe.loc[long_cond, ['enter_long', 'enter_tag']] = [1, 'V5_LONG_QUANTUM']
        dataframe.loc[short_cond, ['enter_short', 'enter_tag']] = [1, 'V5_SHORT_QUANTUM']
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if len(dataframe) == 0: return None
        last = dataframe.iloc[-1]
        
        # 1. ANTI-ZOMBIES
        trade_duration = (current_time - trade.open_date_utc).total_seconds() / 3600
        if trade_duration > 6.0: return 'TIME_EXIT_6H'
        
        # 2. SALIDA TARGET DINÁMICA (Profit Slider en base a fuerza RSI 1m)
        if not trade.is_short:
            # Rsi strength: 0.0 (RSI 50) a 1.0 (RSI 0). A más fuerza bajista, target más bajo.
            rsi_strength = max(0, (50 - last.get('rsi_1m', 50)) / 50)
            target_zone = last['bb_mid'] + (last['bb_upper'] - last['bb_mid']) * (1.0 - rsi_strength) * 0.5
            if current_profit > 0 and last['close'] >= target_zone:
                return 'TARGET_DYNAMIC'
        else:
            # RSI strength: 0.0 (RSI 50) a 1.0 (RSI 100). A más fuerza alcista, target más alto.
            rsi_strength = max(0, (last.get('rsi_1m', 50) - 50) / 50)
            target_zone = last['bb_mid'] - (last['bb_mid'] - last['bb_lower']) * (1.0 - rsi_strength) * 0.5
            if current_profit > 0 and last['close'] <= target_zone:
                return 'TARGET_DYNAMIC'
        
        # 3. SALIDA SECUNDARIA (MID ESTRICTA SI RSI CRUZA LA MEDIA)
        if current_profit > 0 and last.get('rsi_1m', 50) > 50 and not trade.is_short and last['close'] >= last['bb_mid']: return 'TARGET_MID_SAFE'
        if current_profit > 0 and last.get('rsi_1m', 50) < 50 and trade.is_short and last['close'] <= last['bb_mid']: return 'TARGET_MID_SAFE'

        # 4. SALIDA AIRBAG (Persistencia Breakout)
        if current_profit < -0.035:
            if not trade.is_short and last.get('airbag_long_trigger', 0) == 1: return 'AIRBAG_1M_DUMP'
            if trade.is_short and last.get('airbag_short_trigger', 0) == 1: return 'AIRBAG_1M_PUMP'
        
        # Nota: La salida MACRO ha sido erradicada porque esta estrategia vivirá 
        # dentro de un sandbox temporal de puro Lateralismo, garantizado por Chacal_Control.
        return None

    def leverage(self, *args, **kwargs) -> float:
        return 5.0
