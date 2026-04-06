# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
"""
CHACAL VOLUME HUNTER - PC EDITION
=================================
- BASADA EN: Chacal_Adaptive_V3 (AWS LOGIC)
- ENFOQUE: BULL / LATERAL con VOLUMEN REAL
- MOTOR: Correlación con BTC + Atraso Reversión
- ESPECIFICA PARA PC: Sin modo Escudo Bear (el servidor se encarga de eso)
"""
import numpy as np
import pandas as pd
from pandas import DataFrame
from datetime import datetime, timedelta
from typing import Optional, Any, Dict
import talib.abstract as ta
from freqtrade.strategy import IStrategy, DecimalParameter, IntParameter
from freqtrade.persistence import Trade

class ChacalVolumeHunter_V1(IStrategy):
    INTERFACE_VERSION = 3
    can_short = False # SOLO LONGS en PC (Bull/Lateral)
    use_custom_exit = True
    use_custom_stoploss = True
    # --- PROTECCIÓN DE GANANCIAS (EL CAJERO AUTOMÁTICO) ---
    trailing_stop = True
    trailing_stop_positive = 0.175
    trailing_stop_positive_offset = 0.226
    trailing_only_offset_is_reached = True

    position_adjustment_enable = True

    # --- HYPEROPTABLE PARAMETERS (OPTIMIZADOS +8.54% BULL) ---
    stoploss_atr_mult = DecimalParameter(1.0, 2.5, default=1.388, space='sell', load=True)
    rsi_buy_min = IntParameter(15, 35, default=20, space='buy', load=True)
    btc_threshold_mult = DecimalParameter(1.0, 2.5, default=1.429, space='buy', load=True)
    exit_rsi_level     = IntParameter(70, 95, default=75, space='sell', load=True)

    # DCA Control para recuperación de retrocesos en Bull
    dca_enabled = True
    max_dca_orders = 2
    dca_drop_mult = DecimalParameter(1.5, 4.0, default=2.807, space='buy', load=True)

    # --- VOLUMEN Y CORRELACIÓN (DNA V3) ---
    w_corr  = DecimalParameter(0.30, 0.60, default=0.597, space='buy', load=True)
    w_atr   = DecimalParameter(0.10, 0.40, default=0.183, space='buy', load=True)
    corr_window = 144 # 12 horas en 5m
    
    stoploss = -0.99 
    timeframe = '5m'
    inf_timeframe = '1h'
    max_open_trades = 8 # Ajustado a 8 según pedido del usuario
    startup_candle_count: int = 144
    _btc_cache: Dict[str, Any] = {}

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # 1. BASE INDICATORS
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=14)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['volume_mean'] = dataframe['volume'].rolling(30).mean()
        
        # 2. BTC DATA (Merge sincrónico seguro sin bugs de cache de Backtesting)
        btc_5m = self.dp.get_pair_dataframe(pair="BTC/USDT:USDT", timeframe=self.timeframe).copy()
        btc_1h = self.dp.get_pair_dataframe(pair="BTC/USDT:USDT", timeframe=self.inf_timeframe).copy()
        
        if not btc_5m.empty:
            btc_5m['btc_5m_rsi'] = ta.RSI(btc_5m, timeperiod=14)
            btc_5m['btc_5m_std'] = btc_5m['close'].pct_change().rolling(24).std()
            btc_5m['btc_5m_close'] = btc_5m['close']
            dataframe = pd.merge(dataframe, btc_5m[['date', 'btc_5m_rsi', 'btc_5m_std', 'btc_5m_close']], on='date', how='left')
        else:
            dataframe['btc_5m_rsi'] = 50
            dataframe['btc_5m_std'] = 0.002
            dataframe['btc_5m_close'] = dataframe['close']
            
        if not btc_1h.empty:
            btc_1h['btc_rsi_1h'] = ta.RSI(btc_1h, timeperiod=14)
            btc_1h['btc_change_1h'] = btc_1h['close'].pct_change()
            # Alinear timeframe 1h hacia 5m
            btc_1h.set_index('date', inplace=True)
            aligned_1h = btc_1h[['btc_rsi_1h', 'btc_change_1h']].reindex(dataframe['date']).ffill()
            dataframe['btc_rsi_1h'] = aligned_1h['btc_rsi_1h'].values
            dataframe['btc_change_1h'] = aligned_1h['btc_change_1h'].values
        else:
            dataframe['btc_rsi_1h'] = 50
            dataframe['btc_change_1h'] = 0

        # Llenar vacíos generados al inicio
        dataframe.fillna({'btc_5m_rsi': 50, 'btc_5m_std': 0.002, 'btc_rsi_1h': 50, 'btc_change_1h': 0}, inplace=True)

        # 3. ATRASO REAL Y CORRELACIÓN
        dataframe['atraso_real'] = dataframe['btc_5m_close'].pct_change(5) - dataframe['close'].pct_change(5)
        
        btc_ret = dataframe['btc_5m_close'].pct_change()
        pair_ret = dataframe['close'].pct_change()
        dataframe['corr_btc'] = pair_ret.rolling(self.corr_window).corr(btc_ret).fillna(0.8)

        # 4. RISK PRESSURE SCORE
        atr_pct = dataframe['atr'] / dataframe['close']
        atr_roll = atr_pct.rolling(self.corr_window).rank(pct=True).fillna(0.5)
        corr_inv = (1 - dataframe['corr_btc']).clip(0, 1)
        
        dataframe['risk_pressure_score'] = (
            float(self.w_corr.value) * corr_inv + 
            float(self.w_atr.value) * atr_roll
        ).clip(0, 1)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dynamic_threshold = dataframe['btc_5m_std'] * float(self.btc_threshold_mult.value)
        
        # Filtro de Calidad (Punto Dulce: 1.3x de Volumen Extra)
        volume_guard = dataframe['volume'] > (dataframe['volume_mean'] * 1.3)
        risk_guard = dataframe['risk_pressure_score'] < 0.40 

        # --- BULL-ONLY MARKET GUARD ---
        is_bull_market = (dataframe['btc_rsi_1h'] > 45) & (dataframe['btc_change_1h'] > -0.015)

        # Lógica BULL ATRASO
        bull_long = (
            is_bull_market &
            (dataframe['btc_5m_rsi'] > 55) & 
            (dataframe['atraso_real'] > dynamic_threshold) &
            (dataframe['atraso_real'].shift(1) <= dynamic_threshold) &
            volume_guard &
            risk_guard
        )

        # Lógica LATERAL RSI
        lateral_long = (
            is_bull_market &
            (dataframe['btc_5m_rsi'].between(45, 55)) &
            (dataframe['rsi'] < self.rsi_buy_min.value) &
            volume_guard
        )

        dataframe.loc[bull_long, 'enter_long'] = 1
        dataframe.loc[bull_long, 'enter_tag'] = 'BULL_VOLUME_ATRASO'
        
        dataframe.loc[lateral_long, 'enter_long'] = 1
        dataframe.loc[lateral_long, 'enter_tag'] = 'LATERAL_VOLUME_SCALP'

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Salida por profit técnico RSI optimizable
        dataframe.loc[dataframe['rsi'] > self.exit_rsi_level.value, 'exit_long'] = 1
        return dataframe

    def custom_stoploss(self, pair: str, trade: Trade, current_time: datetime,
                        current_rate: float, current_profit: float, **kwargs) -> float:
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or dataframe.empty: return self.stoploss
        
        last = dataframe.iloc[-1]
        atr_stop = (last['atr'] * float(self.stoploss_atr_mult.value)) / last['close']
        
        # Piso mínimo de 0.8% para evitar cierres instantáneos por ATR mini
        # Sin el techo fijo de antes que ahogaba los trades ganadores
        return -max(0.008, atr_stop)

    def adjust_trade_position(self, trade: Trade, current_time: datetime,
                               current_rate: float, current_profit: float,
                               min_stake: Optional[float], max_stake: float,
                               current_entry_rate: float, **kwargs) -> Optional[float]:
        # Usamos dca_drop_mult como porcentaje de caída (ej: 2.807 -> -0.02807)
        drop_threshold = -(float(self.dca_drop_mult.value) / 100)
        if not self.dca_enabled or current_profit > drop_threshold: 
            return None
        
        if trade.nr_of_successful_entries < self.max_dca_orders:
            return trade.stake_amount * 1.5
            
        return None
