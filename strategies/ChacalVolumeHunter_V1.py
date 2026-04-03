# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
"""
CHACAL VOLUME HUNTER - PC EDITION (ADAPTIVE SUPER BULL)
======================================================
- BASADA EN: Chacal_Adaptive_V3
- ENFOQUE: BULL / LATERAL con VOLUMEN REAL
- ADAPTATIVO: Detecta Super Bull y relaja trailing/RSI-exit.
- DCA: Apagado temporalmente por órdenes del Capitán.
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
    can_short = False 
    use_custom_exit = True
    use_custom_stoploss = True
    
    # Trailing base. El stop loss custom de ATR anula esto cuando sea necesario.
    trailing_stop = True
    trailing_stop_positive = 0.015
    trailing_stop_positive_offset = 0.04
    trailing_only_offset_is_reached = True
    
    position_adjustment_enable = True

    # ROI: Solo como red de seguridad para trades eternos. El trailing es el jefe de salida.
    minimal_roi = {
        "0": 0.50,
        "720": 0.20,
        "1440": 0.10
    }

    # --- HYPEROPTABLE BASE (GANADORES FEB 2024) ---
    stoploss_atr_mult = DecimalParameter(1.0, 3.0, default=1.514, space='sell', load=True)
    rsi_buy_min = IntParameter(15, 60, default=31, space='buy', load=True)
    btc_threshold_mult = DecimalParameter(0.8, 2.5, default=0.869, space='buy', load=True)
    exit_rsi_level = IntParameter(60, 95, default=92, space='sell', load=True)

    # --- DCA APAGADO ---
    dca_enabled = False
    max_dca_orders = 0
    dca_drop_mult = DecimalParameter(1.5, 3.5, default=2.124, space='buy', load=True)

    # --- VOLUMEN Y CORRELACIÓN ---
    w_corr  = DecimalParameter(0.30, 0.60, default=0.575, space='buy', load=True)
    w_atr   = DecimalParameter(0.10, 0.40, default=0.308, space='buy', load=True)
    corr_window = 144 
    
    # --- TRAILING (OPTUNA VALUES) ---
    trailing_stop_positive = 0.302
    trailing_stop_positive_offset = 0.391
    inf_timeframe = '1h'
    max_open_trades = 8
    startup_candle_count: int = 144
    _btc_cache: Dict[str, Any] = {}

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=14)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['ema_20'] = ta.EMA(dataframe, timeperiod=20)
        dataframe['volume_mean'] = dataframe['volume'].rolling(30).mean()
        
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
            btc_1h.set_index('date', inplace=True)
            aligned_1h = btc_1h[['btc_rsi_1h', 'btc_change_1h']].reindex(dataframe['date']).ffill()
            dataframe['btc_rsi_1h'] = aligned_1h['btc_rsi_1h'].values
            dataframe['btc_change_1h'] = aligned_1h['btc_change_1h'].values
        else:
            dataframe['btc_rsi_1h'] = 50
            dataframe['btc_change_1h'] = 0

        dataframe.fillna({'btc_5m_rsi': 50, 'btc_5m_std': 0.002, 'btc_rsi_1h': 50, 'btc_change_1h': 0}, inplace=True)
        dataframe['atraso_real'] = dataframe['btc_5m_close'].pct_change(5) - dataframe['close'].pct_change(5)
        
        btc_ret = dataframe['btc_5m_close'].pct_change()
        pair_ret = dataframe['close'].pct_change()
        dataframe['corr_btc'] = pair_ret.rolling(self.corr_window).corr(btc_ret).fillna(0.8)

        atr_pct = dataframe['atr'] / dataframe['close']
        atr_roll = atr_pct.rolling(self.corr_window).rank(pct=True).fillna(0.5)
        corr_inv = (1 - dataframe['corr_btc']).clip(0, 1)
        
        dataframe['risk_pressure_score'] = (
            float(self.w_corr.value) * corr_inv + 
            float(self.w_atr.value) * atr_roll
        ).clip(0, 1)

        # -----------------------------------------------------
        # GEN MUTANTE ADAPTATIVO: DETECCIÓN DE SUPER BULL CORREGIDA
        # -----------------------------------------------------
        # ¡ERROR PEGASO!: Antes exigía que el BTC subiera > 1% POR HORA. Eso jamás pasaba.
        # Ahora el detector se vuelve realista: Simplemente si el RSI de 1H de BTC está furioso (>60).
        dataframe['is_super_bull'] = (dataframe['btc_rsi_1h'] > 60)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dynamic_threshold = dataframe['btc_5m_std'] * float(self.btc_threshold_mult.value)
        volume_guard = dataframe['volume'] > (dataframe['volume_mean'] * 1.3)
        risk_guard = dataframe['risk_pressure_score'] < 0.40 
        is_bull_market = (dataframe['btc_rsi_1h'] > 45) & (dataframe['btc_change_1h'] > -0.015)

        dataframe['hour'] = dataframe['date'].dt.hour
        # time_guard = (dataframe['hour'] >= 6) & (dataframe['hour'] < 20)
        time_guard = True  # TEST 24/7 MODE: Sin restricción horaria

        # 1. LATERAL NORMAL
        lateral_long = (
            is_bull_market &
            time_guard &
            (~dataframe['is_super_bull']) & 
            (dataframe['btc_5m_rsi'].between(45, 55)) &
            (dataframe['rsi'] < self.rsi_buy_min.value) &
            volume_guard
        )

        # 2. BULL NORMAL (Atraso conservador)
        bull_long = (
            is_bull_market &
            time_guard &
            (~dataframe['is_super_bull']) &
            (dataframe['btc_5m_rsi'] > 55) & 
            (dataframe['atraso_real'] > dynamic_threshold) &
            (dataframe['atraso_real'].shift(1) <= dynamic_threshold) &
            volume_guard &
            risk_guard
        )

        # 3. SUPER BULL FOMO (Francotirador Exponencial de Alts)
        # INYECTADO: Filtro de Correlatividad (risk_guard) y Volume Guard. 
        # Las Alts son más exponenciales pero requieren confirmación de que están acopladas a la onda de BTC.
        super_bull_long = (
            dataframe['is_super_bull'] &
            time_guard &
            (dataframe['rsi'] < (self.rsi_buy_min.value + 40)) &
            (dataframe['close'] > dataframe['ema_20']) &
            volume_guard &
            risk_guard
        )

        dataframe.loc[lateral_long, 'enter_long'] = 1
        dataframe.loc[lateral_long, 'enter_tag'] = 'LATERAL_VOLUME'
        
        dataframe.loc[bull_long, 'enter_long'] = 1
        dataframe.loc[bull_long, 'enter_tag'] = 'BULL_ATRASO'
        
        dataframe.loc[super_bull_long, 'enter_long'] = 1
        dataframe.loc[super_bull_long, 'enter_tag'] = 'SUPER_BULL_FOMO'

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # TOMA DE GANANCIAS INTELIGENTE: Si la moneda llega a un pico de sobrecompra, vende.
        # Esto es lo que nos faltaba. Sin esto, el bot siempre esperaba que la moneda bajara
        # para sacarnos por trailing stop, convirtiendo trades ganadores en perdedores.
        exit_long = (
            (dataframe['rsi'] > self.exit_rsi_level.value) &
            (dataframe['volume'] > 0)
        )
        
        dataframe.loc[exit_long, 'exit_long'] = 1
        dataframe.loc[exit_long, 'exit_tag'] = 'RSI_OVERBOUGHT'
        
        return dataframe

    # ==============================================================
    # LEVERAGE ACTIVO: x5 FIJO (Ordenes directas del Capitán)
    # ==============================================================
    def leverage(self, pair, current_time, current_rate, proposed_leverage,
                  max_leverage, entry_tag, side, **kwargs) -> float:
         return min(5.0, max_leverage)

    def custom_stoploss(self, pair: str, trade: Trade, current_time: datetime,
                        current_rate: float, current_profit: float, **kwargs) -> float:
        """
        TRAILING ADAPTATIVO ESCALONADO:
        - Si sube de golpe (>10%), asegura fuerte con 3% de holgura.
        - Si está en ganancia leve, deja 15% de holgura para no asfixiar el trade en Super Bull.
        - En pérdida: da 6% de margen para permitir que el DCA en -3% actúe.
        """
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        is_super_bull = False
        
        if dataframe is not None and not dataframe.empty:
            last_candle = dataframe.iloc[-1]
            is_super_bull = bool(last_candle.get('is_super_bull', False))

        # EN GANANCIA: Dejamos el trailing laxo para que suba hasta la estratosfera, 
        # pero si hace un rally loco (> OFFSET OPTUNA), lo estrangulamos.
        if current_profit > self.trailing_stop_positive_offset:
            return self.trailing_stop_positive
        elif current_profit > 0.05:
            return -0.15 if is_super_bull else -0.08
        elif current_profit > 0.0:
            return -0.15 if is_super_bull else -0.08 
            
        # EN PÉRDIDA: Cortamos rápido el sangrado ahora que no hay DCA.
        if dataframe is None or dataframe.empty:
            return self.stoploss

        last_candle = dataframe.iloc[-1]
        base_atr_stop = (last_candle['atr'] * float(self.stoploss_atr_mult.value)) / last_candle['close']
        adaptive_stop = base_atr_stop * (1.5 if is_super_bull else 1.0)
        
        return -max(0.015, adaptive_stop)

    def adjust_trade_position(self, trade: Trade, current_time: datetime,
                              current_rate: float, current_profit: float,
                              min_stake: Optional[float], max_stake: float,
                              **kwargs) -> Optional[float]:
        # DCA ELIMINADO DEFINITIVAMENTE PARA REGRESAR A RESULTADOS POSITIVOS
        return None