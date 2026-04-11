# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
import numpy as np
import pandas as pd
from pandas import DataFrame
import talib.abstract as ta
from freqtrade.strategy import IStrategy, DecimalParameter, IntParameter
from freqtrade.persistence import Trade
from datetime import datetime
from typing import Optional, Any, Dict

class ChacalVolumeHunter_V1(IStrategy):
    """
    CHACAL VOLUME HUNTER - PC EDITION (SYNCHRONIZED & PROTECTED)
    ESTADO: MASTER OPTIMIZADA (Drawdown < 11%)
    """
    INTERFACE_VERSION = 3
    can_short = False 
    use_custom_exit = True
    use_custom_stoploss = True
    trailing_stop = True
    trailing_stop_positive = 0.03
    trailing_stop_positive_offset = 0.07
    trailing_only_offset_is_reached = True
    minimal_roi = {'0': 0.50}
    stoploss = -0.99
    
    # --- Parámetros de Inflexión de Mercado (Optimizado Epoch 116) ---
    macro_rsi_bull = IntParameter(50, 75, default=70, space='buy', load=True) # Punto de cambio a FOMO
    fomo_rsi_max = IntParameter(65, 85, default=68, space='buy', load=True)   # Techo de entrada FOMO
    
    # --- Parámetros Buy (Optimizado Epoch 116) ---
    btc_threshold_mult = DecimalParameter(0.8, 2.5, default=0.869, space='buy', load=True)
    rsi_buy_min = IntParameter(15, 60, default=31, space='buy', load=True)
    w_corr  = DecimalParameter(0.3, 0.6, default=0.575, space='buy', load=True)
    w_atr   = DecimalParameter(0.1, 0.4, default=0.308, space='buy', load=True)

    # --- Parámetros Sell/Exit ---
    exit_rsi_level = IntParameter(60, 95, default=92, space='sell', load=True)
    stoploss_atr_mult = DecimalParameter(1.0, 3.0, default=1.514, space='sell', load=True)
    
    timeframe = '5m'
    inf_timeframe = '1h'
    max_open_trades = 8

    def informative_pairs(self):
        return [
            ('BTC/USDT:USDT', self.inf_timeframe), 
            ('BTC/USDT:USDT', self.timeframe),
            ('BTC/USDT:USDT', '1m')
        ]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=14)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['ema_20'] = ta.EMA(dataframe, timeperiod=20)
        dataframe['ema_13'] = ta.EMA(dataframe, timeperiod=13)
        dataframe['volume_mean'] = dataframe['volume'].rolling(30).mean()
        
        btc_5m = self.dp.get_pair_dataframe(pair='BTC/USDT:USDT', timeframe=self.timeframe).copy()
        btc_1h = self.dp.get_pair_dataframe(pair='BTC/USDT:USDT', timeframe=self.inf_timeframe).copy()
        
        if not btc_5m.empty:
            btc_5m['btc_rsi'] = ta.RSI(btc_5m, timeperiod=14)
            btc_5m['btc_std'] = btc_5m['close'].pct_change(fill_method=None).rolling(24).std()
            btc_5m_reduced = btc_5m[['date', 'btc_rsi', 'btc_std', 'close']].rename(columns={'close': 'close_btc'})
            dataframe = pd.merge(dataframe, btc_5m_reduced, on='date', how='left')
        
        if not btc_1h.empty:
            btc_1h['btc_rsi_1h'] = ta.RSI(btc_1h, timeperiod=14)
            btc_1h['btc_ema_50_1h'] = ta.EMA(btc_1h, timeperiod=50) # FILTRO MACRO
            btc_1h['btc_delta'] = btc_1h['close'].pct_change(fill_method=None)
            dataframe = pd.merge(dataframe, btc_1h[['date', 'btc_rsi_1h', 'btc_ema_50_1h', 'btc_delta']], on='date', how='left')
        
        # Corrección: fillna y comprobación de columnas
        dataframe.fillna({'btc_rsi_1h': 50, 'btc_delta': 0, 'btc_rsi': 50, 'btc_std': 0.002}, inplace=True)
        if 'btc_ema_50_1h' not in dataframe.columns:
             dataframe['btc_ema_50_1h'] = dataframe['close'] * 1.5
        
        if 'close_btc' not in dataframe.columns: dataframe['close_btc'] = dataframe['close']
            
        # --- MICRO 1m (Gatillo de Seguridad Cuántico del Par) ---
        inf_1m = self.dp.get_pair_dataframe(pair=metadata['pair'], timeframe='1m').copy()
        if not inf_1m.empty:
            inf_1m['rsi_1m'] = ta.RSI(inf_1m, timeperiod=14)
            inf_1m['ema_slow_1m'] = ta.EMA(inf_1m, timeperiod=50)
            inf_1m['vol_mean_1m'] = inf_1m['volume'].rolling(10).mean()
            
            # --- SCORING SNIPER BULL ---
            # 1. Agotamiento de venta (RSI < 30 en 1m)
            inf_1m['exhaust_long'] = (inf_1m['rsi_1m'] < 30).astype(int)
            # 2. Divergencia Alcista (Precio baja, RSI sube)
            inf_1m['div_bullish'] = ((inf_1m['close'] <= inf_1m['close'].shift(1)) & (inf_1m['rsi_1m'] > inf_1m['rsi_1m'].shift(1))).astype(int)
            
            # Airbag Persistencia
            inf_1m['airbag_long_trigger'] = ((inf_1m['close'] < inf_1m['ema_slow_1m']) & (inf_1m['volume'] > inf_1m['vol_mean_1m'])).rolling(6).min()
            
            inf_1m_vars = inf_1m[['date', 'rsi_1m', 'exhaust_long', 'div_bullish', 'airbag_long_trigger']]
            
            dataframe = pd.merge_asof(
                dataframe.sort_values('date'),
                inf_1m_vars.sort_values('date'),
                on='date',
                direction='backward'
            )
        else:
            dataframe['rsi_1m'] = 50
            dataframe['exhaust_long'] = 0
            dataframe['div_bullish'] = 0
            dataframe['airbag_long_trigger'] = 0
            
        # El atraso ahora es una medida de fuerza, no de debilidad
        dataframe['atraso'] = dataframe['close'].pct_change(12, fill_method=None)
        
        # FILTRO MACRO IMPLACABLE
        dataframe['is_macro_bull'] = False
        dataframe.loc[(dataframe['btc_ema_50_1h'] > 0) & (dataframe['close_btc'] > dataframe['btc_ema_50_1h']), 'is_macro_bull'] = True
        
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # 1. BULL SNIPER DIP (Transplante de ADN del Bear)
        bull_sniper_dip = (
            dataframe['is_macro_bull'] & 
            (dataframe['btc_delta'] > -0.005) &  # BTC no tiene que estar colapsando
            (dataframe['exhaust_long'] == 1) &  # Ya hubo agotamiento en 1m
            (dataframe['div_bullish'] == 1) &    # Hay divergencia alcista en 1m
            (dataframe['rsi'] < 45)             # No entramos si ya voló demasiado
        )
        # 2. SUPER BULL FOMO (Permisivo para captar el rally)
        super_bull_long = (
            dataframe['is_macro_bull'] & 
            (dataframe['btc_rsi_1h'] > self.macro_rsi_bull.value) & 
            (dataframe['rsi'] < self.fomo_rsi_max.value) & 
            (dataframe['close'] > dataframe['ema_20']) &
            (dataframe['volume'] > dataframe['volume_mean'])
        )

        dataframe.loc[bull_sniper_dip, 'enter_long'] = 1
        dataframe.loc[bull_sniper_dip, 'enter_tag'] = 'BULL_SNIPER_DIP'
        dataframe.loc[super_bull_long, 'enter_long'] = 1
        dataframe.loc[super_bull_long, 'enter_tag'] = 'SUPER_BULL_FOMO'
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        exit_long = (
            (dataframe['rsi'] > self.exit_rsi_level.value)
        )
        dataframe.loc[exit_long, 'exit_long'] = 1
        dataframe.loc[exit_long, 'exit_tag'] = 'RSI_OVERBOUGHT'
        return dataframe

    def custom_exit(self, pair: str, trade: Trade, current_time: datetime, current_rate: float,
                    current_profit: float, **kwargs):
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        last_candle = dataframe.iloc[-1].squeeze()

        # ROTACIÓN DE CAPITAL (DESACTIVADA PARA BULL AGRESIVO)
        # if current_profit > 0.05:
        #     if last_candle['close'] < last_candle['ema_13']:
        #         return 'TECHNICAL_ROTATION'
                
        # --- ZOMBIE & DUMP KILL SWITCHES ---
        time_opened_h = (current_time - trade.open_date_utc).total_seconds() / 3600
        
        # 1. ZOMBIE KILLER: 48h y perdiendo > 5%
        if time_opened_h > 48.0 and current_profit < -0.05:
            return 'ZOMBIE_48H_LOSS'
            
        # 3. QUANTUM AIRBAG (1m): Si EL PAR rompe su estructura micro
        # RELAJADO: Solo si la pérdida es real (-4%) para dar aire al trade (antes -1%)
        if last_candle.get('airbag_long_trigger', 0) == 1 and current_profit < -0.04:
            return 'QUANTUM_AIRBAG_DUMP'

        # 2. PANIC DUMP AIRBAG (Reducido a -25% apalancado)
        if current_profit < -0.25:
            return 'PANIC_DUMP_LOSS'

        return None

    def leverage(self, pair, current_time, current_rate, proposed_leverage, max_leverage, entry_tag, side, **kwargs) -> float:
        return 5.0

    def custom_stoploss(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        if current_profit > self.trailing_stop_positive_offset:
            return self.trailing_stop_positive
        return self.stoploss

    def adjust_trade_position(self, trade: Trade, current_time: datetime, current_rate: float, current_profit: float, min_stake: Optional[float], max_stake: float, **kwargs) -> Optional[float]:
        return None