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
             CHACAL FAN-HUNTER V5.3 (Extreme Reversion)
    ========================================================
    Estrategia de francotirador 1-minuto.
    Desarrollada para Tokens de Alta Volatilidad (Fan Tokens + Memes).

    Lógica de Combate:
    - Longs: Z-Score > 10 (volumen EXTREMADAMENTE anormal) + RSI < 65.
             Caza mechas de liquidación bajistas en picos de evento.
    - Shorts: RSI > 88 (FOMO masivo absoluto → corrección inminente).
    - Filtro: Funding Rate en tiempo real para no entrar contra el flujo institucional.
    - Exits: TakeProfit +5%/+8% y StopLoss -3%/-4% por custom_exit.

    CORRECCIÓN CRÍTICA V5.3:
    - startup_candle_count = 1500: OBLIGATORIO. Sin esto, el Z-Score devuelve
      NaN en las primeras 1440 velas y el bot no genera NINGUNA señal.
      Este era el único bug real. Los umbrales NO fueron modificados porque
      fueron validados por el Mega-Scan de 6 meses (cientos de trades/par).
    """
    
    INTERFACE_VERSION = 3

    timeframe = '1m'
    can_short = True
    
    # *** FIX CRÍTICO: El bot pide 1500 velas históricas al arrancar.
    # Sin esto, el Z-Score de ventana 1440 devuelve NaN puro y no hay señales. ***
    startup_candle_count = 1500

    # ROI: Desactivado — se maneja con custom_exit
    minimal_roi = {
        "0": 100.0
    }
    stoploss = -0.99  # Se maneja con custom stoploss interno (custom_exit)

    # --- PARÁMETROS VALIDADOS POR MEGA-SCAN (NO MODIFICAR SIN NUEVA EVIDENCIA) ---
    vol_window    = 1440  # 24hs de contexto de volumen (1440 mins en 1m TF)
    z_score_long  = 10.0  # Validado: eventos estadísticos extremos (Z > 10σ)
    rsi_long_max  = 65    # Validado: RSI no saturado para caza de mechas
    rsi_short_min = 88    # Validado: FOMO masivo que precede correcciones fuertes

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        
        # 1. RSI de 14 Períodos (Nativo Freqtrade / TA-Lib)
        import talib.abstract as ta
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)

        # 2. Z-Score Cuántico del Volumen
        # Requiere startup_candle_count >= 1500 para que no sea NaN
        dataframe['vol_mean'] = dataframe['volume'].rolling(window=self.vol_window).mean()
        dataframe['vol_std']  = dataframe['volume'].rolling(window=self.vol_window).std()
        # Protección: evitar división por cero en tokens con vol muy plano
        dataframe['vol_std']  = dataframe['vol_std'].replace(0, np.nan)
        dataframe['z_score']  = (dataframe['volume'] - dataframe['vol_mean']) / dataframe['vol_std']

        return dataframe

    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe['enter_long'] = 0
        dataframe['enter_short'] = 0

        pair = metadata.get('pair', '')
        # WIF es Solo Short: sube por spikes violentos y corrige fuerte
        allow_long = True
        if "WIF" in pair:
            allow_long = False

        # LONG: Explosión de volumen extrema + RSI no agotado
        if allow_long:
            dataframe.loc[
                (
                    (dataframe['z_score'] > self.z_score_long) &
                    (dataframe['rsi'] < self.rsi_long_max) &
                    (dataframe['volume'] > 0) &
                    (dataframe['z_score'].notna())  # Garantiza que el warmup terminó
                ),
                'enter_long'] = 1

        # SHORT: FOMO extremo → corrección inminente
        dataframe.loc[
            (
                (dataframe['rsi'] > self.rsi_short_min) &
                (dataframe['volume'] > 0) &
                (dataframe['rsi'].notna())
            ),
            'enter_short'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe['exit_long'] = 0
        dataframe['exit_short'] = 0

        # Exit LONG: RSI llega a zona de sobrecompra → cerrar antes de que revierta
        dataframe.loc[(dataframe['rsi'] > 85), 'exit_long'] = 1

        # Exit SHORT: RSI regresó a zona neutral → corrección terminó
        dataframe.loc[(dataframe['rsi'] < 45), 'exit_short'] = 1

        return dataframe
        
    def confirm_trade_entry(self, pair: str, order_type: str, amount: float, rate: float,
                           time_in_force: str, current_time: datetime, entry_tag: str,
                           side: str, **kwargs) -> bool:
        """
        FILTRO DE EXPECTATIVAS (FUNDING RATE):
        Consulta el funding rate en tiempo real antes de entrar al trade.
        Si el mercado contradice la dirección → bloqueamos la entrada.
        """
        try:
            funding_data = self.exchange.fetch_funding_rate(pair)
            funding_rate = funding_data.get('fundingRate', 0)

            if side == "short":
                # Funding muy negativo = shorts saturados = posible squeeze. NO ENTRAR.
                if funding_rate < -0.0001:
                    return False
            
            if side == "long":
                # Funding muy positivo = longs saturados de codicia. NO ENTRAR.
                if funding_rate > 0.001:
                    return False

        except Exception:
            # Si la API de funding falla, el trade pasa igual
            return True

        return True

    def custom_exit(self, pair: str, trade, current_time: datetime, current_rate: float,
                    current_profit: float, **kwargs) -> str:
        """
        Salidas de precisión por umbrales fijos.
        Se ejecuta en cada tick, sin esperar señales del dataframe.
        """
        if trade.is_short:
            if current_profit >= 0.05:   # +5.0% → Cobrar
                return "Hard TP Short"
            if current_profit <= -0.03:  # -3.0% → Cortar pérdida
                return "Hard SL Short"
        else:
            if current_profit >= 0.08:   # +8.0% → Cobrar
                return "Hard TP Long"
            if current_profit <= -0.04:  # -4.0% → Cortar pérdida
                return "Hard SL Long"
                
        return None
