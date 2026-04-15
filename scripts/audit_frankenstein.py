"""
AUDITOR DEL FRANKENSTEIN
Analiza la calidad de los periodos laterales en el dataset sintético.
Criterios de validación:
1. Rango del precio (max-min)/avg < 5% en cada periodo
2. Pendiente de la EMA (slope) < umbral (tendencias disfrazadas)
3. Distribución de duración de los periodos
"""
import pandas as pd
import numpy as np

# Cargar datos originales (descargados previamente)
# Vamos a leer el dataset Frankenstein ya construido y auditar los periodos
DATA_PATH = 'PROJECT_SNIPER_AWS/user_data/data/franken_data/futures/BTC_USDT_USDT-1m-futures.feather'

print("Cargando dataset Frankenstein...")
df = pd.read_feather(DATA_PATH)
df['date'] = pd.to_datetime(df['date'], utc=True) if 'date' in df.columns else pd.to_datetime(df.index, utc=True)

print(f"\n📊 ESTADÍSTICAS DEL DATASET:")
print(f"   Total de velas: {len(df):,}")
print(f"   Período: {df['date'].min()} → {df['date'].max()}")
print(f"   Días equivalentes: {len(df)/1440:.1f}")

# Calcular indicadores de calidad por ventana de 60 velas (1h)
WINDOW = 60
df['rolling_max'] = df['close'].rolling(WINDOW).max()
df['rolling_min'] = df['close'].rolling(WINDOW).min()
df['rolling_avg'] = df['close'].rolling(WINDOW).mean()
df['rango_pct'] = (df['rolling_max'] - df['rolling_min']) / df['rolling_avg'] * 100

# EMA slope (cambio % de la EMA cada 60 velas)
df['ema50'] = df['close'].ewm(span=50).mean()
df['ema_slope'] = df['ema50'].pct_change(WINDOW).abs() * 100

# Clasificar calidad
df_valid = df.dropna()
lateral_duro = df_valid[df_valid['rango_pct'] < 2.0]    # Muy lateral (< 2% de rango)
lateral_medio = df_valid[(df_valid['rango_pct'] >= 2.0) & (df_valid['rango_pct'] < 4.0)]  # Lateral normal
tendencia_lenta = df_valid[df_valid['rango_pct'] >= 4.0] # Tendencia disfrazada

print(f"\n🔬 CALIDAD DE PERIODOS (Ventana de 1h / 60 velas):")
print(f"   ✅ Lateral DURO (rango < 2%):    {len(lateral_duro):>6,} velas ({len(lateral_duro)/len(df_valid)*100:.1f}%)")
print(f"   🟡 Lateral MEDIO (2-4% rango):   {len(lateral_medio):>6,} velas ({len(lateral_medio)/len(df_valid)*100:.1f}%)")
print(f"   🔴 Tendencia DISFRAZADA (> 4%):  {len(tendencia_lenta):>6,} velas ({len(tendencia_lenta)/len(df_valid)*100:.1f}%)")

print(f"\n📐 RANGO PROMEDIO DE PRECIO (1h):")
print(f"   Media:   {df_valid['rango_pct'].mean():.2f}%")
print(f"   Mediana: {df_valid['rango_pct'].median():.2f}%")
print(f"   P90:     {df_valid['rango_pct'].quantile(0.90):.2f}%")

print(f"\n📐 PENDIENTE DE EMA (movimiento %):")
print(f"   Media:   {df_valid['ema_slope'].mean():.3f}%")
print(f"   Mediana: {df_valid['ema_slope'].median():.3f}%")
print(f"   P90:     {df_valid['ema_slope'].quantile(0.90):.3f}%")

print(f"\n📉 PEORES PERIODOS (snapshots más volátiles):")
worst = df_valid.nlargest(5, 'rango_pct')[['date','close','rango_pct','ema_slope']]
print(worst.to_string(index=False))

print(f"\n✅ VEREDICTO FINAL:")
pct_contaminado = len(tendencia_lenta)/len(df_valid)*100
if pct_contaminado > 30:
    print(f"   🚨 DATASET CONTAMINADO: {pct_contaminado:.1f}% de velas no son lateral puro.")
    print(f"   El generador Frankenstein necesita un filtro de PENDIENTE DE EMA.")
elif pct_contaminado > 15:
    print(f"   ⚠️  DATASET PARCIALMENTE CONTAMINADO: {pct_contaminado:.1f}% de ruido.")
else:
    print(f"   ✅ DATASET ACEPTABLE: Solo {pct_contaminado:.1f}% de contaminación.")
