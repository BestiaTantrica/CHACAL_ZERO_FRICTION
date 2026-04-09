@echo off
setlocal enabledelayedexpansion

REM --- Parametros del contenedor ---
set CONTAINER_NAME=chacal_volume_dryrun
set USER_DATA=%~dp0user_data
set STRATEGIES=%CD%\..\strategies

echo [Volume Hunter] Deteniendo contenedor previo (si existe)...
docker rm -f %CONTAINER_NAME% >nul 2>&1

echo [Volume Hunter] Arrancando contenedor en modo Dry Run...
docker run -d --name %CONTAINER_NAME% --cpus 2 --memory 7g -p 8080:8080 --restart unless-stopped ^
  -v "%USER_DATA%:/freqtrade/user_data" ^
  -v "%STRATEGIES%:/freqtrade/user_data/strategies" ^
  freqtradeorg/freqtrade:stable trade ^
  --config /freqtrade/user_data/configs/config_backtest.json ^
  --strategy ChacalVolumeHunter_V1 --dry-run

if %ERRORLEVEL% neq 0 (
  echo [Volume Hunter] Error al arrancar el contenedor. Revisar logs.
  exit /b 1
)

echo [Volume Hunter] Contenedor iniciado correctamente con limits --cpus 2 --memory 7g.
echo [Volume Hunter] Puedes seguir los logs con: docker logs -f %CONTAINER_NAME%
endlocal