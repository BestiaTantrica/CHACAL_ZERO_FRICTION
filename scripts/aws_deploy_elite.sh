#!/bin/bash
# 🦅 SCRIPT DE DESPLIEGUE ELITE FICT V4.0
# Limpia, Purga y Sincroniza la Instancia AWS

IP="54.94.193.76"
KEY="/home/chacal/llave-sao-paulo.pem"
USER="ubuntu"

echo "🚀 INICIANDO PURGA DE ZOMBIES EN AWS..."
ssh -i $KEY $USER@$IP << 'EOF'
    # Detener servicios
    sudo systemctl stop ft-lateral ft-bear ft-bull chacal-control
    
    # Matar procesos colgados (Zombies)
    sudo pkill -9 freqtrade || true
    
    # Limpiar archivos de bloqueo
    find /home/ubuntu/chacal/user_data/ -name "*.lock" -delete
    
    # Eliminar servicio lateral obsoleto
    sudo systemctl disable ft-lateral
    sudo rm -f /etc/systemd/system/ft-lateral.service
    
    # REPARAR SERVICIOS (PATH FIX)
    cat << 'SVC' | sudo tee /etc/systemd/system/ft-bear.service
[Unit]
Description=Freqtrade Bear Specialist
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/chacal
ExecStart=/home/ubuntu/chacal/.venv/bin/freqtrade trade --config /home/ubuntu/chacal/user_data/configs/config.json --strategy ChacalSniper_Bear44 --strategy-path /home/ubuntu/chacal/user_data/strategies
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SVC

    cat << 'SVC' | sudo tee /etc/systemd/system/ft-bull.service
[Unit]
Description=Freqtrade Bull Specialist
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/chacal
ExecStart=/home/ubuntu/chacal/.venv/bin/freqtrade trade --config /home/ubuntu/chacal/user_data/configs/config.json --strategy ChacalVolumeHunter_V1 --strategy-path /home/ubuntu/chacal/user_data/strategies
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SVC

    sudo systemctl daemon-reload
    echo "✅ Servicios reparados con rutas reales."
EOF

echo "📤 SUBIENDO CEREBRO V4.0 SNIPER KING..."
scp -i $KEY LAB_BACKTEST_ANUAL/user_data/strategies/ChacalSniper_Bear44.py $USER@$IP:~/chacal/user_data/strategies/
scp -i $KEY LAB_BACKTEST_ANUAL/user_data/strategies/ChacalVolumeHunter_V1.py $USER@$IP:~/chacal/user_data/strategies/
scp -i $KEY scripts/chacal_orchestrator.py $USER@$IP:~/chacal/scripts/

echo "🔄 RE-ARMANDO SERVICIOS..."
ssh -i $KEY $USER@$IP << 'EOF'
    sudo systemctl restart chacal-control
    echo "🚀 SISTEMA ELITE EN LÍNEA. +527% ROI ACTIVADO."
EOF
