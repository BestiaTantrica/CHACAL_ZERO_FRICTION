#!/bin/bash
# ==============================================================================
# SCRIPT DE PROVISIÓN: CHACAL ORACLE MICRO INSTANCE (Always Free)
# ==============================================================================
# Uso: Ejecutar como root o con sudo en la nueva instancia Ubuntu de Oracle.
# ==============================================================================

set -e # Detener en caso de error

echo "🦅 Iniciando provisión de Instancia Chacal Lateral (Oracle Micro)..."

# 1. SWAP: CRÍTICO PARA LA INSTANCIA DE 1GB RAM
if [ ! -f /swapfile ]; then
    echo "🛠️ 1. Creando archivo Swap de 4GB para evitar colapsos de RAM..."
    sudo fallocate -l 4G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    
    # Ajustar "swappiness" para que solo use swap en emergencias reales
    sudo sysctl vm.swappiness=10
    echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
else
    echo "✅ 1. Archivo Swap ya existe."
fi

# 2. ACTUALIZACIÓN DEL SISTEMA Y DEPENDENCIAS BASE
echo "🛠️ 2. Actualizando repositorios e instalando herramientas base..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv python3-dev build-essential \
    libssl-dev git wget tmux htop sqlite3 screen

# 3. CREACIÓN DEL ENTORNO VIRTUAL PRIVADO
echo "🛠️ 3. Creando entorno virtual aislado de Python (~/.venv_chacal)..."
cd ~
if [ ! -d ".venv_chacal" ]; then
    python3 -m venv .venv_chacal
    # Asegurarnos de que el venv use la última versión de PIP
    .venv_chacal/bin/python -m pip install --upgrade pip
else
    echo "✅ 3. Entorno virtual ya existe."
fi

# 4. INSTALACIÓN DEL MOTOR BASE
echo "🛠️ 4. Instalando motor balístico (ccxt, pandas, numpy, freqtrade)..."
.venv_chacal/bin/pip install wheel
# Freqtrade instala todo lo necesario (ccxt, pandas, numpy, ta-lib)
.venv_chacal/bin/pip install numpy pandas ccxt freqtrade ta-lib-bin

# 5. ESTRUCTURA DE CARPETAS OPERATIVAS
echo "🛠️ 5. Armando estructura de directorios del orquestador..."
mkdir -p ~/CHACAL_LATERAL_AWS/user_data/strategies
mkdir -p ~/CHACAL_LATERAL_AWS/user_data/data
mkdir -p ~/CHACAL_LATERAL_AWS/user_data/logs
mkdir -p ~/CHACAL_LATERAL_AWS/user_data/configs

echo "=============================================================================="
echo "🎯 PROVISIÓN COMPLETADA CON ÉXITO!"
echo "Instrucciones siguientes:"
echo "1. El sistema tiene 1GB RAM + 4GB de SWAP (Inmune a colapsos OOM)."
echo "2. El motor se ejecuta usando: ~/.venv_chacal/bin/freqtrade"
echo "3. Use 'tmux' o 'screen' para mantener el bot corriendo de fondo."
echo "=============================================================================="
