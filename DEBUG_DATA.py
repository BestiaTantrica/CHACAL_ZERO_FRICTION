import json
import os

path = r"C:\CHACAL_ZERO_FRICTION\user_data\data\binance\futures\BTC_USDT-5m-futures.json"
print("--- TEST DE ACCESO A DATOS ---")
if os.path.exists(path):
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            print(f"ESTADO: OK - Archivo encontrado")
            print(f"RUTA: {path}")
            print(f"CANTIDAD DE VELAS: {len(data)}")
            if len(data) > 0:
                import datetime
                df0 = datetime.datetime.fromtimestamp(data[0][0]/1000).strftime('%Y-%m-%d %H:%M:%S')
                df1 = datetime.datetime.fromtimestamp(data[-1][0]/1000).strftime('%Y-%m-%d %H:%M:%S')
                print(f"RANGO: {df0} HASTA {df1}")
    except Exception as e:
        print(f"ERROR AL LEER: {str(e)}")
else:
    print(f"ERROR: No existe {path}")
    base_dir = r"C:\CHACAL_ZERO_FRICTION\user_data\data\binance\futures"
    if os.path.exists(base_dir):
        print("\nArchivos encontrados en la carpeta (Primeros 10):")
        print("\n".join(os.listdir(base_dir)[:10]))
    else:
        print(f"ERROR FATAL: Ni siquiera existe la carpeta {base_dir}")
