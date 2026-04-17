@echo off
SET PEM_KEY=skills\llave-sao-paulo.pem
SET SERVER=ubuntu@129.80.104.116
SET REMOTE_PATH=/home/ubuntu/CHACAL_LATERAL_AWS

echo [🚀] INICIANDO SINCRONIZACION ORACLE - CHACAL LATERAL V5
echo [🛰️] Destino: %SERVER%

echo [1/2] Subiendo Configuracion y Estrategia...
scp -i %PEM_KEY% -o StrictHostKeyChecking=no config_v5_oracle.json %SERVER%:%REMOTE_PATH%/config.json
scp -i %PEM_KEY% -o StrictHostKeyChecking=no strategies\ChacalLateral_V5.py %SERVER%:%REMOTE_PATH%/user_data/strategies/

echo [2/2] Reiniciando Servicio ft-lateral en Oracle...
ssh -i %PEM_KEY% -o StrictHostKeyChecking=no %SERVER% "sudo systemctl restart ft-lateral && echo [✅] Chacal Lateral Reiniciado con V5"

echo [🏁] SINCRONIZACION FINALIZADA
