# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---
import numpy as np
import pandas as pd
from datetime import datetime
from freqtrade.strategy import (IStrategy, IntParameter, DecimalParameter)

class ChacalFanHunter_V5(IStrategy):
    """
    ========================================================
             CHACAL FAN-HUNTER V5 (Extreme Reversion)
    ========================================================
    Estrategia de francotirador 1-minuto.
    Desarrollada exclusivamente para Tokens de Alta Volatilidad (Eventos/Memes).
    
    Lógica de Combate:
    - Longs: Detecta un volumen EXTREMADAMENTE ANORMAL (Z-Score > 10) 
             combinado con RSI no saturado (< 65). Caza mechas de liquidación bajistas.
    - Shorts: Dispara automáticamente frente a fomo masivo absoluto (RSI > 88).
    - Exits: Retiros tácticos rápidos a la zona media del RSI o Take Profits fijos.
    """
    
    INTERFACE_VERSION = 3

    timeframe = '1m'
    can_short = True
    
    # ROI: Reemplazado por salidas tácticas de RSI
    minimal_roi = {
        "0": 100.0  # El ROI dinámico se maneja en custom_exit
    }
    stoploss = -0.99  # Se maneja con custom stoploss interno

    # --- PARÁMETROS V4 CRÍTICOS VALIDADOS EN LABORATORIO ---
    vol_window = 1440  # Mapea las últimas 24hs (1440 mins)
    z_score_long = 10.0
    rsi_long_max = 65
    rsi_short_min = 88

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        
        # 1. RSI de 14 Períodos (Nativo Freqtrade / TA-Lib)
        import talib.abstract as ta
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)

        # 2. Z-Score Cuántico del Volumen
        dataframe['vol_mean'] = dataframe['volume'].rolling(window=self.vol_window).mean()
        dataframe['vol_std']  = dataframe['volume'].rolling(window=self.vol_window).std()
        dataframe['z_score']  = (dataframe['volume'] - dataframe['vol_mean']) / dataframe['vol_std']

        return dataframe

    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe['enter_long'] = 0
        dataframe['enter_short'] = 0

        pair = metadata.get('pair', '')
        # --- DOCTRINA ELITE: Restricciones de entrada por Token ---
        # Solo Short: Tokens que suben por spikes violentos y corrigen fuerte (WIF).
        allow_long = True
        if "WIF" in pair:
            allow_long = False

        # LONG: Explosión de volumen gigante + RSI no agotado (cacería de mechas)
        if allow_long:
            dataframe.loc[
                (
                    (dataframe['z_score'] > self.z_score_long) &
                    (dataframe['rsi'] < self.rsi_long_max) &
                    (dataframe['volume'] > 0)
                ),
                'enter_long'] = 1

        # SHORT: Fomo absurdo (Entrando en zona de corrección extrema)
        dataframe.loc[
            (
                (dataframe['rsi'] > self.rsi_short_min) &
                (dataframe['volume'] > 0)
            ),
            'enter_short'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe['exit_long'] = 0
        dataframe['exit_short'] = 0

        # Exit LONG: El fomo cedió y estamos listos para cobrar
        dataframe.loc[
            (
                (dataframe['rsi'] > 85)
            ),
            'exit_long'] = 1

        # Exit SHORT: La pánico cedió, se revierte
        dataframe.loc[
            (
                (dataframe['rsi'] < 45)
            ),
            'exit_short'] = 1

        return dataframe
        
    def confirm_trade_entry(self, pair: str, order_type: str, amount: float, rate: float,
                           time_in_force: str, current_time: datetime, entry_tag: str,
                           side: str, **kwargs) -> bool:
        """
        FILTRO DE EXPECTATIVAS (FUNDING RATE):
        Juega con el miedo/codicia del mercado usando datos institucionales en tiempo real.
        """
        try:
            # Obtener el funding rate actual desde la API de Binance
            # Esto evita entrar en Shorts si el funding es negativo (nos cobran a nosotros)
            # Y potencia entrar en Shorts si el funding es alto positivo (el mercado está muy Bull)
            funding_data = self.exchange.fetch_funding_rate(pair)
            funding_rate = funding_data.get('fundingRate', 0)

            if side == "short":
                # Si el funding es muy negativo (< -0.01%), los shorts están saturados. NO ENTRAR.
                if funding_rate < -0.0001:
                    return False
            
            if side == "long":
                # Si el funding es muy positivo (> 0.1%), los longs están saturados de codicia. NO ENTRAR.
                if funding_rate > 0.001:
                    return bool(0)

        except Exception:
            # Si falla la API por laguna razón, pasamos el trade igual
            return True

        return True

    def custom_exit(self, pair: str, trade, current_time: datetime, current_rate: float,
                    current_profit: float, **kwargs) -> str:
        """
        Salidas de precisión por umbrales fijos (Hard TakeProfit / StopLoss).
        """
        if trade.is_short:
            if current_profit >= 0.05:  # +5.0%
                return "Hard TP Short"
            if current_profit <= -0.03: # -3.0% Stoploss manual
                return "Hard SL Short"
        else:
            if current_profit >= 0.08:  # +8.0%
                return "Hard TP Long"
            if current_profit <= -0.04: # -4.0% Stoploss manual
                return "Hard SL Long"
                
        return None
