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

class ChacalLateral_V4(IStrategy):
    """
    CHACAL LATERAL V4 - ARQUITECTURA CUÁNTICA
    Implementación del Scoring Probabilístico sin filtros binarios.
    Evita Trailing Stop y Lookahead bias en 1 minuto.
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

    # --- DNA MACRO (5m y 1h) ---
    band_proximity    = DecimalParameter(0.0005, 0.005, default=0.002, space='buy', optimize=True)
    lateral_threshold = DecimalParameter(0.015, 0.05, default=0.039, space='buy', optimize=True)
    bb_width_max      = DecimalParameter(0.02, 0.15, default=0.08, space='buy', optimize=True)
    bb_width_min      = DecimalParameter(0.001, 0.02, default=0.005, space='buy', optimize=True)
    adx_limit         = IntParameter(15, 40, default=21, space='buy', optimize=True)

    # --- MIRA 1m (SCORING) ---
    score_threshold_long  = IntParameter(1, 3, default=1, space='buy', optimize=True)
    score_threshold_short = IntParameter(1, 3, default=2, space='sell', optimize=True)
    
    # --- FILTRO 5m (El protector original) ---
    rsi_long_max      = IntParameter(20, 40, default=30, space='buy', optimize=True)
    rsi_short_min     = IntParameter(40, 80, default=70, space='sell', optimize=True)

    stoploss = -0.05 
    timeframe = '5m'
    minimal_roi = {"0": 100} 
    max_open_trades = 8

    def informative_pairs(self):
        pairs = self.dp.current_whitelist()
        informative = [('BTC/USDT:USDT', '1h')]
        for p in pairs:
            informative.append((p, '1m'))
        return informative

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # 1. MACRO BTC (1h)
        btc_1h = self.dp.get_pair_dataframe(pair='BTC/USDT:USDT', timeframe='1h')
        if not btc_1h.empty:
            btc_1h['ema50'] = ta.EMA(btc_1h, timeperiod=50)
            dataframe = pd.merge(dataframe,
                btc_1h[['date', 'close', 'ema50']].rename(columns={'close': 'btc_close'}),
                on='date', how='left').ffill()
            dataframe['is_lateral'] = (
                (dataframe['btc_close'] > dataframe['ema50']*(1-self.lateral_threshold.value)) &
                (dataframe['btc_close'] < dataframe['ema50']*(1+self.lateral_threshold.value))
            )
        else:
            dataframe['is_lateral'] = False

        # 2. CORE (5m)
        bollinger = ta.BBANDS(dataframe, timeperiod=20, nbdevup=2.0, nbdevdn=2.0)
        dataframe['bb_upper'], dataframe['bb_mid'], dataframe['bb_lower'] = bollinger['upperband'], bollinger['middleband'], bollinger['lowerband']
        dataframe['bb_width'] = (dataframe['bb_upper'] - dataframe['bb_lower']) / dataframe['bb_mid']
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['adx'] = ta.ADX(dataframe, timeperiod=14)
        
        dataframe['prep_ready'] = (
            (dataframe['is_lateral'] == True) & 
            (dataframe['bb_width'] < self.bb_width_max.value) & 
            (dataframe['bb_width'] > self.bb_width_min.value) & 
            (dataframe['adx'] > self.adx_limit.value)
        ).astype(int)

        # 3. MICRO / MIRA INSTITUCIONAL (1m) a través de merge backward
        inf_1m = self.dp.get_pair_dataframe(pair=metadata['pair'], timeframe='1m')
        
        if not inf_1m.empty:
            inf_1m['rsi_1m'] = ta.RSI(inf_1m, timeperiod=14)
            inf_1m['ema_slow_1m'] = ta.EMA(inf_1m, timeperiod=50)
            inf_1m['atr_1m'] = ta.ATR(inf_1m, timeperiod=14)
            inf_1m['vol_mean_1m'] = inf_1m['volume'].rolling(10).mean()
            
            # --- COMPONENTES DEL SCORING ---
            # 1. Price Action Confirmation
            inf_1m['pa_bullish'] = (inf_1m['close'] > inf_1m['open']).astype(int)
            inf_1m['pa_bearish'] = (inf_1m['close'] < inf_1m['open']).astype(int)
            # 2. Agotamiento Micro
            inf_1m['exhaust_long'] = (inf_1m['rsi_1m'] < 30).astype(int)
            inf_1m['exhaust_short'] = (inf_1m['rsi_1m'] > 70).astype(int)
            # 3. Divergencia Simple (Fuerza Relativa vs Cierre Anterior)
            inf_1m['div_bullish'] = ((inf_1m['close'] <= inf_1m['close'].shift(1)) & (inf_1m['rsi_1m'] > inf_1m['rsi_1m'].shift(1))).astype(int)
            inf_1m['div_bearish'] = ((inf_1m['close'] >= inf_1m['close'].shift(1)) & (inf_1m['rsi_1m'] < inf_1m['rsi_1m'].shift(1))).astype(int)
            
            # 4. Airbag Persistencia (3 velas por debajo de EMA con volumen)
            inf_1m['airbag_long_trigger'] = ((inf_1m['close'] < inf_1m['ema_slow_1m']) & (inf_1m['volume'] > inf_1m['vol_mean_1m'])).rolling(3).min()
            inf_1m['airbag_short_trigger'] = ((inf_1m['close'] > inf_1m['ema_slow_1m']) & (inf_1m['volume'] > inf_1m['vol_mean_1m'])).rolling(3).min()
            
            inf_1m_vars = inf_1m[['date', 'rsi_1m', 'ema_slow_1m', 'atr_1m', 'volume', 'vol_mean_1m', 'close', 
                                  'pa_bullish', 'pa_bearish', 'exhaust_long', 'exhaust_short', 'div_bullish', 'div_bearish',
                                  'airbag_long_trigger', 'airbag_short_trigger']]
            inf_1m_vars = inf_1m_vars.rename(columns={'volume': 'vol_1m', 'close': 'close_1m'})
            
            # MAGIA: Merge seguro contra el futuro.
            dataframe = pd.merge_asof(dataframe, inf_1m_vars, on='date', direction='backward')
            
            # Construcción del SCORING
            dataframe['score_long'] = dataframe['pa_bullish'] + dataframe['exhaust_long'] + dataframe['div_bullish']
            dataframe['score_short'] = dataframe['pa_bearish'] + dataframe['exhaust_short'] + dataframe['div_bearish']
        else:
            # Fallback seguro
            dataframe['score_long'] = 0
            dataframe['score_short'] = 0
            dataframe['ema_slow_1m'] = 0
            dataframe['close_1m'] = 0
            dataframe['vol_1m'] = 0
            dataframe['vol_mean_1m'] = 0
            dataframe['airbag_long_trigger'] = 0
            dataframe['airbag_short_trigger'] = 0

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # GATILLO MEDIANTE SCORING (Score >= 2 requiere confluencia, y devolvemos filtro RSI 5m original)
        long_cond = (
            (dataframe['prep_ready'] == 1) & 
            (dataframe['close'] <= dataframe['bb_lower'] * (1 + self.band_proximity.value)) & 
            (dataframe['rsi'] < self.rsi_long_max.value) &
            (dataframe['score_long'] >= self.score_threshold_long.value)
        )
        
        short_cond = (
            (dataframe['prep_ready'] == 1) & 
            (dataframe['close'] >= dataframe['bb_upper'] * (1 - self.band_proximity.value)) & 
            (dataframe['rsi'] > self.rsi_short_min.value) &
            (dataframe['score_short'] >= self.score_threshold_short.value)
        )

        dataframe.loc[long_cond, ['enter_long', 'enter_tag']] = [1, 'V4_LONG_QUANTUM']
        dataframe.loc[short_cond, ['enter_short', 'enter_tag']] = [1, 'V4_SHORT_QUANTUM']
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
        
        # 2. SALIDA NÚCLEO (TARGET_MID)
        if trade.is_short and last['close'] <= last['bb_mid'] and current_profit > 0: return 'TARGET_MID'
        if not trade.is_short and last['close'] >= last['bb_mid'] and current_profit > 0: return 'TARGET_MID'
        
        # 3. SALIDA AIRBAG (Diferenciar Breakout vs Mecha en 1m)
        if current_profit < -0.035:  # Darle más margen al trade (Mejor que -0.015 para Mean Reversion)
            if not trade.is_short:
                # LONG Atrapado: Breakout bajista real mantenido por 3 minutos (persistencia)
                if last.get('airbag_long_trigger', 0) == 1:
                    return 'AIRBAG_1M_DUMP'
            else:
                # SHORT Atrapado: Breakout alcista real mantenido por 3 minutos (persistencia)
                if last.get('airbag_short_trigger', 0) == 1:
                    return 'AIRBAG_1M_PUMP'
        
        # 4. SALIDA MACRO
        if not last.get('is_lateral', False): return 'MACRO_BREAKOUT'
        
        return None

    def leverage(self, *args, **kwargs) -> float:
        return 5.0
