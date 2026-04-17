#!/bin/bash
# Script para iniciar túnel SOCKS5 hacia Brasil
PEM_KEY=~/.ssh/llave-sao-paulo.pem
BRAZIL_SERVER=ubuntu@54.94.193.76

# Cerrar túneles antiguos
pkill -f 'ssh -i .* -N -D 1080'

echo "[🛰️] Iniciando Túnel SOCKS5 en primer plano..."
# Ejecutamos ssh sin & para que systemd controle el proceso
exec ssh -i "$PEM_KEY" -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=10 -N -D 1080 "$BRAZIL_SERVER"
