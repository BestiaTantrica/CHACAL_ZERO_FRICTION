@echo off
SET PEM_KEY=skills\llave-sao-paulo.pem
SET SERVER=ubuntu@54.94.193.76
SET REMOTE_PATH=/home/ubuntu/chacal

echo [🚀] INICIANDO SINCRONIZACION ELITE - CHACAL V5
echo [🛰️] Destino: %SERVER%

echo [1/3] Subiendo Estrategias V5...
scp -i %PEM_KEY% strategies\ChacalSniper_BearV5.py %SERVER%:%REMOTE_PATH%/user_data/strategies/
scp -i %PEM_KEY% strategies\ChacalVolumeHunter_V5.py %SERVER%:%REMOTE_PATH%/user_data/strategies/

echo [2/3] Sincronizando Datos (Agosto 2024)...
scp -i %PEM_KEY% PROJECT_SNIPER_AWS\user_data\data\binance\futures\*.feather %SERVER%:%REMOTE_PATH%/user_data/data/binance/futures/

echo [3/3] Reiniciando Servicios en AWS...
ssh -i %PEM_KEY% %SERVER% "sudo systemctl daemon-reload && sudo systemctl restart ft-bear && echo [✅] Sniper Bear Reiniciado con V5"

echo [🏁] OPERACION FINALIZADA CON EXITO (ZERO FRICTION)
pause
