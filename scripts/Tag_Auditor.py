import json
import pandas as pd

def analyze_tags(json_path):
    with open(json_path) as f:
        data = json.load(f)
    
    # Encontrar la estrategia (puede variar el nombre en el dict)
    strat_name = list(data['strategy'].keys())[0]
    stats = data['strategy'][strat_name]['results_per_enter_tag']
    
    print(f"\n📊 AUDITORÍA DE TAGS PARA {strat_name}:")
    print(f"{'Tag':<25} | {'Trades':<8} | {'WinRate':<10} | {'Profit Abs':<12}")
    print("-" * 65)
    
    for val in stats:
        tag = val['key']
        wr = val['wins'] / (val['wins'] + val['losses'] + val['draws']) if (val['wins'] + val['losses'] + val['draws']) > 0 else 0
        print(f"{tag:<25} | {val['trades']:<8} | {wr*100:>8.1f}% | {val['profit_total_abs']:>11.2f} USDT")

if __name__ == "__main__":
    analyze_tags('LAB_BACKTEST_ANUAL/user_data/backtest_results/backtest-result-sniper_bear.json')
    analyze_tags('LAB_BACKTEST_ANUAL/user_data/backtest_results/backtest-result-volume_hunter.json')
