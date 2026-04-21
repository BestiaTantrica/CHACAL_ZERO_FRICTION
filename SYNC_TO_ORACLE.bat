@echo off
SET PEM_KEY=skills\llave-sao-paulo.pem
SET SERVER=ubuntu@129.80.104.116
SET REMOTE_PATH=/home/ubuntu/CHACAL_LATERAL_AWS

echo [🚀] INICIANDO SINCRONIZACION ORACLE - CHACAL LATERAL V5
echo [🛰️] Destino: %SERVER%

echo [1/2] Subiendo Configuracion y Estrategia Fan-Hunter V5...
scp -i %PEM_KEY% -o StrictHostKeyChecking=no config_chacal_arena.json %SERVER%:%REMOTE_PATH%/config.json
scp -i %PEM_KEY% -o StrictHostKeyChecking=no strategies\ChacalFanHunter_V5.py %SERVER%:%REMOTE_PATH%/user_data/strategies/

echo [2/2] Reiniciando Servicio en Oracle (ft-fan-hunter)...
ssh -i %PEM_KEY% -o StrictHostKeyChecking=no %SERVER% "sudo systemctl daemon-reload && sudo systemctl restart ft-fan-hunter && echo [✅] Chacal Fan-Hunter Elite 6 Operando"

echo [🏁] SINCRONIZACION FINALIZADA
