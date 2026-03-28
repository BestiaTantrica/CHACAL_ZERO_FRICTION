import sqlite3
import pandas as pd
import json

def analyze_trades(db_path):
    conn = sqlite3.connect(db_path)
    # Ver las tablas
    cursor = conn.cursor()
    cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table';\")
    tables = cursor.fetchall()
    
    # Obtener los ultimos 10 trades
    try:
        query = \"\"\"
        SELECT pair, strategy, enter_tag, close_date, close_profit_pct, is_open, fee_open, fee_close
        FROM trades 
        ORDER BY id DESC LIMIT 20
        \"\"\"
        df = pd.read_sql_query(query, conn)
        print(\"--- ULTIMOS 20 TRADES (AUDITORIA) ---\")
        print(df.to_string())
        
        # Resumen de profit total reciente
        profit_query = \"SELECT SUM(close_profit_pct) as total_profit_pct FROM trades WHERE is_open=0\"
        total_p = pd.read_sql_query(profit_query, conn)
        print(f\"\nProfit Total Acumulado (Cerrados): {total_p['total_profit_pct'].iloc[0]:.2f}%\")
        
    except Exception as e:
        print(f\"Error al leer trades: {e}\")
    finally:
        conn.close()

if __name__ == '__main__':
    analyze_trades(r'C:\CHACAL_ZERO_FRICTION\user_data\tradesv3_aws.sqlite')
