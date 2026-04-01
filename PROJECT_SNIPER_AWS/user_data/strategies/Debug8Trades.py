from pandas import DataFrame
from freqtrade.strategy import IStrategy

class Debug8Trades(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True
    timeframe = '5m'
    stoploss = -0.10
    minimal_roi = {"0": 1.0}

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Entrar cada 50 velas para asegurar solapamiento de 8 trades
        dataframe.loc[dataframe.index % 50 == 0, 'enter_short'] = 1
        dataframe.loc[dataframe.index % 50 == 0, 'enter_tag'] = 'DEBUG_FORCE'
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Salir a las 40 velas (mantener posición 40 velas)
        dataframe.loc[dataframe.index % 50 == 40, 'exit_short'] = 1
        return dataframe
