import shutil, os

src = r"C:\CHACAL_ZERO_FRICTION\user_data\data\binance\futures"
dst = r"C:\CHACAL_ZERO_FRICTION\PROJECT_SNIPER_AWS\user_data\data\binance\futures"

print(f"Copiando {src} -> {dst}")
if os.path.exists(dst):
    shutil.rmtree(dst)
shutil.copytree(src, dst)
print(f"LISTO. Archivos copiados: {len(os.listdir(dst))}")
