import pandas as pd
import numpy as np

# Load the consolidated backtest data
df = pd.read_csv('c:/CHACAL_ZERO_FRICTION/trifasico_backtest_consolidado.csv')

# Filter by LATERAL regime
# Looking at the sample, regime_at_open has values like 'LATERAL', 'BULL', etc.
lateral_df = df[df['regime_at_open'] == 'LATERAL'].copy()

# Group by pair and calculate metrics
metrics = lateral_df.groupby('pair').agg({
    'profit_ratio': ['count', 'mean', 'sum'],
    'drawdown_pct': 'max'
})

# Flatten column names
metrics.columns = ['trades_count', 'avg_profit_ratio', 'total_profit_ratio', 'max_drawdown_pct']

# Calculate Win Rate
def calc_win_rate(group):
    wins = (group['profit_ratio'] > 0).sum()
    total = len(group)
    return wins / total if total > 0 else 0

win_rates = lateral_df.groupby('pair').apply(calc_win_rate)
metrics['win_rate'] = win_rates

# Sort by total profit ratio descending
metrics = metrics.sort_values(by='total_profit_ratio', ascending=False)

print("--- METRICS FOR LATERAL REGIME ---")
print(metrics)

# Also check for some volatility metric if possible or just the total performance
# The user wants "cantidades first" (quantities)
