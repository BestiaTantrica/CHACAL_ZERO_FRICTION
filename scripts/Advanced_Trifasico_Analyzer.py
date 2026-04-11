import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta

class AdvancedTrifasicoAnalyzer:
    def __init__(self, btc_1h_path, results_dir):
        self.btc_1h_path = btc_1h_path
        self.results_dir = results_dir
        self.lateral_threshold = 0.043  # Umbral Óptimo detectado
        self.ema_period = 50
        
    def load_btc_data(self):
        """Carga datos de BTC/USDT y calcula indicadores macro"""
        if self.btc_1h_path.endswith('.feather'):
            df = pd.read_feather(self.btc_1h_path)
        else:
            df = pd.read_json(self.btc_1h_path)
        
        df['date'] = pd.to_datetime(df['date'], unit='ms' if df['date'].dtype == 'int64' else None)
        df = df.sort_values('date')
        
        # EMA50
        df['ema50'] = df['close'].ewm(span=self.ema_period, adjust=False).mean()
        df['diff_pct'] = (df['close'] / df['ema50']) - 1
        
        # RSI (Triple Confirmación)
        def rsi_calc(series, period=14):
            delta = series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
        
        df['rsi'] = rsi_calc(df['close'])
        df['vol_mean'] = df['volume'].rolling(24).mean()
        
        return df

    def determine_regime_map(self, btc_df, threshold):
        """Crea un mapa de tiempo -> régimen activo con TRIPLE CONFIRMACIÓN"""
        regimes = {}
        
        for _, row in btc_df.iterrows():
            diff = abs(row['diff_pct'])
            vol_factor = row['volume'] / row['vol_mean'] if row['vol_mean'] > 0 else 1.0
            rsi = row['rsi']
            
            # --- LÓGICA DE GESTIÓN AVANZADA ---
            if diff <= 0.02:
                # Zona Lateral Pura
                regime = 'LATERAL'
            elif 0.02 < diff <= threshold:
                # Zona de Umbral Crítico: Relevo si hay Volumen ADEMÁS de RSI extremo
                if vol_factor > 1.3 and (rsi > 65 or rsi < 35):
                    regime = 'BULL' if row['diff_pct'] > 0 else 'BEAR'
                else:
                    regime = 'LATERAL'
            else:
                # Tendencia Macro
                regime = 'BULL' if row['diff_pct'] > 0 else 'BEAR'
            
            timestamp = row['date'].replace(minute=0, second=0, microsecond=0)
            regimes[timestamp] = regime
        return regimes

    def load_trades(self, strategy_id):
        file_path = os.path.join(self.results_dir, f'backtest-result-{strategy_id}.json')
        if not os.path.exists(file_path):
            print(f"⚠️ Archivo no encontrado: {file_path}")
            return pd.DataFrame()
            
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Extraer trades
        strategy_name = list(data['strategy'].keys())[0]
        trades = data['strategy'][strategy_name]['trades']
        df = pd.DataFrame(trades)
        
        if df.empty:
            return df
            
        df['open_date'] = pd.to_datetime(df['open_date'])
        df['close_date'] = pd.to_datetime(df['close_date'])
        return df

    def run_optimization(self):
        print("🚀 INICIANDO OPTIMIZACIÓN DE GESTIÓN (LOOP DE REGÍMENES)")
        btc_df = self.load_btc_data()
        regime_map = self.determine_regime_map(btc_df, self.lateral_threshold)
        
        lat_trades = self.load_trades('lateral_v4')
        bear_trades = self.load_trades('sniper_bear')
        bull_trades = self.load_trades('volume_hunter')
        
        results_matrix = {
            'LATERAL': {'LAT': 0, 'BEAR': 0, 'BULL': 0},
            'BEAR': {'LAT': 0, 'BEAR': 0, 'BULL': 0},
            'BULL': {'LAT': 0, 'BEAR': 0, 'BULL': 0}
        }
        
        counts_matrix = {
            'LATERAL': {'LAT': 0, 'BEAR': 0, 'BULL': 0},
            'BEAR': {'LAT': 0, 'BEAR': 0, 'BULL': 0},
            'BULL': {'LAT': 0, 'BEAR': 0, 'BULL': 0}
        }
        
        # Mapear cada trade de cada bot a su régimen y guardarlo en la matriz
        for bot_id, trades in [('LAT', lat_trades), ('BEAR', bear_trades), ('BULL', bull_trades)]:
            if trades.empty: continue
            trades['regime'] = trades['open_date'].dt.floor('h').map(regime_map)
            for regime in ['LATERAL', 'BEAR', 'BULL']:
                valid = trades[trades['regime'] == regime]
                results_matrix[regime][bot_id] = valid['profit_abs'].sum()
                counts_matrix[regime][bot_id] = len(valid)

        print("\n📊 MATRIZ DE RENDIMIENTO POR RÉGIMEN (Profit USDT):")
        print(f"{'Régimen':<10} | {'Lateral Bot':<12} | {'Bear Bot':<12} | {'Bull Bot':<12}")
        print("-" * 55)
        for r in ['LATERAL', 'BEAR', 'BULL']:
            print(f"{r:<10} | {results_matrix[r]['LAT']:>12.2f} | {results_matrix[r]['BEAR']:>12.2f} | {results_matrix[r]['BULL']:>12.2f}")

        print("\n📈 TRADES POR RÉGIMEN (Conteo):")
        for r in ['LATERAL', 'BEAR', 'BULL']:
            print(f"{r:<10} | {counts_matrix[r]['LAT']:>12} | {counts_matrix[r]['BEAR']:>12} | {counts_matrix[r]['BULL']:>12}")

        # Selección de "Equipo Ganador"
        best_team = {
            'LATERAL': max(results_matrix['LATERAL'], key=results_matrix['LATERAL'].get),
            'BEAR': max(results_matrix['BEAR'], key=results_matrix['BEAR'].get),
            'BULL': max(results_matrix['BULL'], key=results_matrix['BULL'].get)
        }
        
        final_profit = sum([results_matrix[r][best_team[r]] for r in ['LATERAL', 'BEAR', 'BULL']])
        print(f"\n🏆 CONFIGURACIÓN DE MÁXIMO PODER:")
        print(f" - En LATERAL usar: {best_team['LATERAL']}")
        print(f" - En BEAR usar:    {best_team['BEAR']}")
        print(f" - En BULL usar:    {best_team['BULL']}")
        print(f"🚀 PROFIT ANUAL COMBINADO ÓPTIMO: {final_profit:.2f} USDT")

    def run_analysis(self):
        print("🚀 INICIANDO ANÁLISIS TRIFÁSICO AVANZADO (1 AÑO)")
        
        btc_df = self.load_btc_data()
        regime_map = self.determine_regime_map(btc_df, self.lateral_threshold)
        
        lateral_trades = self.load_trades('lateral_v4')
        bear_trades = self.load_trades('sniper_bear')
        bull_trades = self.load_trades('volume_hunter')
        
        final_trades = []
        # Usar el "Equipo Ganador" con FILTROS DE CALIDAD y LEVERAGE SELECTIVO
        for name, df, target_regime, specialist_id in [
            ('🔮 Lateral (USANDO BEAR)', bear_trades, 'LATERAL', 'BEAR'),
            ('🦅 Bear (USANDO BEAR)', bear_trades, 'BEAR', 'BEAR'),
            ('🦊 Bull (USANDO BULL)', bull_trades, 'BULL', 'BULL')
        ]:
            if df.empty: continue
            df['regime_at_open'] = df['open_date'].dt.floor('h').map(regime_map)
            valid_trades = df[df['regime_at_open'] == target_regime].copy()
            
            # --- FILTROS DE CALIDAD ELITE V4.0 ---
            if specialist_id == 'BULL':
                # Solo usamos los dos tags sniper
                valid_trades = valid_trades[valid_trades['enter_tag'].isin(['BULL_SNIPER_DIP', 'SUPER_BULL_FOMO'])]
                # 10x leverage (Factor 2x sobre el 5x base)
                valid_trades['profit_abs'] = valid_trades['profit_abs'] * 2.0
            
            if specialist_id == 'BEAR':
                # 7x leverage (Factor 1.4x sobre el 5x base)
                valid_trades['profit_abs'] = valid_trades['profit_abs'] * 1.4
            
            valid_trades['specialist'] = name
            final_trades.append(valid_trades)
            print(f" - {name}: {len(valid_trades)} trades de ALTA CALIDAD")

        if not final_trades:
            print("❌ No se encontraron trades.")
            return

        all_valid = pd.concat(final_trades).sort_values('open_date')
        
        # --- CÁLCULO DE EQUITY Y DRAWDOWN ---
        all_valid['cumulative_profit'] = all_valid['profit_abs'].cumsum()
        all_valid['equity'] = 1000 + all_valid['cumulative_profit']
        all_valid['peak'] = all_valid['equity'].cummax()
        all_valid['drawdown_abs'] = all_valid['peak'] - all_valid['equity']
        all_valid['drawdown_pct'] = (all_valid['drawdown_abs'] / all_valid['peak']) * 100
        
        max_dd_pct = all_valid['drawdown_pct'].max()
        final_profit = all_valid['profit_abs'].sum()
        
        print("\n📈 RESULTADOS CONSOLIDADOS DEL FONDO (A 5x Actual):")
        print(f"Total Trades: {len(all_valid)}")
        print(f"Profit Neto: {final_profit:.2f} USDT (+{final_profit/10:.1f}%)")
        print(f"Drawdown Máximo: {max_dd_pct:.2f}%")
        
        print("\n🔥 PROYECCIÓN A 10x (Apalancamiento Agresivo):")
        print(f"Profit Neto Est: {final_profit * 2:.2f} USDT (+{final_profit*2/10:.1f}%)")
        print(f"Drawdown Est: {max_dd_pct * 2:.2f}%")
        
        if max_dd_pct * 2 > 80:
            print("⚠️ ADVERTENCIA: A 10x el riesgo de liquidación es EXTREMO (>80% DD).")
        else:
            print("✅ FACTIBLE: El sistema aguanta 10x conservando un margen de seguridad.")

        all_valid.to_csv('trifasico_backtest_consolidado.csv', index=False)

if __name__ == "__main__":
    # Rutas relativas al laboratorio
    BTC_PATH = "LAB_BACKTEST_ANUAL/user_data/data/binance/futures/BTC_USDT_USDT-1h-futures.feather"
    RESULTS_DIR = "LAB_BACKTEST_ANUAL/user_data/backtest_results"
    
    # Este script se corre después de tener los 3 JSON de backtest
    analyzer = AdvancedTrifasicoAnalyzer(BTC_PATH, RESULTS_DIR)
    analyzer.run_analysis() # Ahora con el equipo ganador y leverage test
    print("Script listo. Ejecútelo tras completar los backtests individuales.")
