@echo off
set CONTAINER_NAME=chacal_volume_dryrun

echo [Volume Hunter] Deteniendo el bot...
docker stop %CONTAINER_NAME% >nul 2>&1
docker rm -f %CONTAINER_NAME% >nul 2>&1

if %ERRORLEVEL% equ 0 (
  echo [Volume Hunter] Contenedor detenido correctamente.
) else (
  echo [Volume Hunter] No se pudo detener o el contenedor ya estaba detenido.
)