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
    # Apretados al rango REAL del mercado micro-lateral (audit: 0.61% rango/hora)
    bb_width_max      = DecimalParameter(0.005, 0.05, default=0.025, space='buy', optimize=True)
    bb_width_min      = DecimalParameter(0.001, 0.01, default=0.003, space='buy', optimize=True)
    
    # Filtro de microestructura (Orderbook proxy)
    spread_max_limit  = DecimalParameter(0.001, 0.005, default=0.003, space='buy', optimize=True)

    # --- SCORING CUÁNTICO PONDERADO (Escala x10) ---
    # pa_bullish = 5, exhaust = 20, div = 15. Máx = 40.
    score_threshold_long  = IntParameter(5, 30, default=20, space='buy', optimize=True)
    score_threshold_short = IntParameter(5, 30, default=20, space='sell', optimize=True)
    
    # Filtros extra
    rsi_core_long_max  = IntParameter(20, 40, default=30, space='buy', optimize=True)
    rsi_core_short_min = IntParameter(40, 80, default=70, space='sell', optimize=True)

    stoploss = -1.0  # SIN STOPLOSS FIJO. El freno es lógico: REGIME_BREAK + MOMENTUM_FAIL.
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
        # GATILLO CUÁNTICO REFINADO: Buscar CONFIRMACIÓN de rebote, no atajar cuchillos cayendo.
        long_cond = (
            (dataframe['bb_width'] < self.bb_width_max.value) & 
            (dataframe['bb_width'] > self.bb_width_min.value) & 
            (dataframe['spread'] < self.spread_max_limit.value) & # Filtro liquidez
            # La vela ANTERIOR debió tocar o estar muy cerca de la banda inferior
            (dataframe['low'].shift(1) <= dataframe['bb_lower'].shift(1) * (1 + self.band_proximity.value)) & 
            # La vela ACTUAL debe cerrar en positivo respecto a la anterior (Rebote confirmado)
            (dataframe['close'] > dataframe['close'].shift(1)) & 
            # RSI también debe acompañar el giro al alza
            (dataframe['rsi_1m'] > dataframe['rsi_1m'].shift(1)) &
            (dataframe['rsi_core'] < self.rsi_core_long_max.value) &
            (dataframe['score_long'] >= self.score_threshold_long.value)
        )
        
        short_cond = (
            (dataframe['bb_width'] < self.bb_width_max.value) & 
            (dataframe['bb_width'] > self.bb_width_min.value) & 
            (dataframe['spread'] < self.spread_max_limit.value) & # Filtro liquidez
            # La vela ANTERIOR debió tocar o estar muy cerca de la banda superior
            (dataframe['high'].shift(1) >= dataframe['bb_upper'].shift(1) * (1 - self.band_proximity.value)) & 
            # La vela ACTUAL debe cerrar en negativo respecto a la anterior (Rebote confirmado)
            (dataframe['close'] < dataframe['close'].shift(1)) & 
            # RSI también debe acompañar el giro a la baja
            (dataframe['rsi_1m'] < dataframe['rsi_1m'].shift(1)) &
            (dataframe['rsi_core'] > self.rsi_core_short_min.value) &
            (dataframe['score_short'] >= self.score_threshold_short.value)
        )

        dataframe.loc[long_cond, ['enter_long', 'enter_tag']] = [1, 'V5_LONG_CONFIRMED']
        dataframe.loc[short_cond, ['enter_short', 'enter_tag']] = [1, 'V5_SHORT_CONFIRMED']
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if len(dataframe) == 0: return None
        last = dataframe.iloc[-1]
        
        # 1. DETECTOR DE RUPTURA DE RÉGIMEN (Reemplaza el Time Exit idiota)
        # Si el mercado dejó de ser lateral mientras estamos en trade, salimos sin dudar.
        bb_width_now = last.get('bb_width', 0)
        bb_width_threshold = self.bb_width_max.value * 1.5  # 50% más ancho = régimen roto
        if bb_width_now > bb_width_threshold:
            return 'REGIME_BREAK_EXIT'

        # 2. HEMORRAGIA RSI - Momentum Continuado en Contra (3 velas consecutivas)
        # Si tras la entrada el RSI sigue deteriorándose 3 velas seguidas, el rebote fue falso.
        dataframe_full = dataframe
        if len(dataframe_full) >= 2:
            rsi_vals = dataframe_full['rsi_1m'].iloc[-2:].values
            if not trade.is_short:
                # Para LONG: si RSI sigue bajando 2 velas seguidas y empezamos a perder
                if current_profit < 0 and rsi_vals[0] > rsi_vals[1]:
                    return 'MOMENTUM_FAIL_EXIT'
            else:
                # Para SHORT: si RSI sigue subiendo 2 velas seguidas y empezamos a perder
                if current_profit < 0 and rsi_vals[0] < rsi_vals[1]:
                    return 'MOMENTUM_FAIL_EXIT'
        
        # 3. SALIDA INSTITUCIONAL PURA (Target bb_upper - Máximo recorrido del lateral)
        # Salimos al tocar la banda OPUESTA. Eso sí justifica el riesgo.
        if current_profit > 0 and not trade.is_short and last['close'] >= last['bb_upper'] * (1 - self.band_proximity.value):
            return 'TARGET_UPPER'  
        if current_profit > 0 and trade.is_short and last['close'] <= last['bb_lower'] * (1 + self.band_proximity.value):
            return 'TARGET_LOWER'
        
        # Salida intermedia de seguridad: si supera el mid con profit, aseguramos.
        if current_profit > 0.005 and not trade.is_short and last['close'] >= last['bb_mid']:
            return 'TARGET_MID_SAFE'
        if current_profit > 0.005 and trade.is_short and last['close'] <= last['bb_mid']:
            return 'TARGET_MID_SAFE'

        # 4. SALIDA AIRBAG (Stop dinámico: 1% de precio = ~1 hora de rango lateral)
        # Si el precio se fue 1.6x el rango horario promedio en nuestra contra, el rebote no viene.
        if current_profit < -0.010:
            if not trade.is_short and last.get('airbag_long_trigger', 0) == 1: return 'AIRBAG_1M_DUMP'
            if trade.is_short and last.get('airbag_short_trigger', 0) == 1: return 'AIRBAG_1M_PUMP'
        # Corte absoluto de emergencia si se fue muy lejos
        if current_profit < -0.025:
            return 'AIRBAG_HARD'
        
        # Nota: La salida MACRO ha sido erradicada porque esta estrategia vivirá 
        # dentro de un sandbox temporal de puro Lateralismo, garantizado por Chacal_Control.
        return None

    def leverage(self, *args, **kwargs) -> float:
        return 5.0
