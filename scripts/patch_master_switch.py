#!/usr/bin/env python3
content = open('/home/ubuntu/chacal/user_data/strategies/ChacalSniper_Bear44.py').read()

old = (
    "            # Lógica del Interruptor\n"
    "            btc_trend_bear = dataframe['btc_close'] < dataframe['btc_ema50']\n"
    "            btc_vol_active = dataframe['btc_atr'] > dataframe['btc_atr_mean']\n"
    "            dataframe['master_bear_switch'] = (btc_trend_bear & btc_vol_active).astype(int)"
)
new = (
    "            # Interruptor siempre activo (replica modo backtest)\n"
    "            dataframe['master_bear_switch'] = 1"
)

if old in content:
    content = content.replace(old, new)
    open('/home/ubuntu/chacal/user_data/strategies/ChacalSniper_Bear44.py', 'w').write(content)
    print("PATCH APLICADO OK - master_bear_switch = 1 siempre")
else:
    print("ERROR: bloque no encontrado, verificar manualmente")
    # Mostrar lineas 128-138 para debug
    lines = open('/home/ubuntu/chacal/user_data/strategies/ChacalSniper_Bear44.py').readlines()
    for i, l in enumerate(lines[126:140], start=127):
        print(f"{i}: {l}", end='')
