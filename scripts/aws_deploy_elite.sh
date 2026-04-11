#!/bin/bash
# 🦅 SCRIPT DE DESPLIEGUE ELITE FICT V4.0
# Limpia, Purga y Sincroniza la Instancia AWS

IP="54.94.193.76"
KEY="skills/llave-sao-paulo.pem"
USER="ubuntu"

echo "🚀 INICIANDO PURGA DE ZOMBIES EN AWS..."
ssh -i $KEY $USER@$IP << 'EOF'
    # Detener servicios
    sudo systemctl stop ft-lateral ft-bear ft-bull chacal-control
    
    # Matar procesos colgados (Zombies)
    sudo pkill -9 freqtrade || true
    
    # Limpiar archivos de bloqueo
    find /home/ubuntu/freqtrade/user_data/ -name "*.lock" -delete
    
    # Eliminar servicio lateral obsoleto
    sudo systemctl disable ft-lateral
    sudo rm -f /etc/systemd/system/ft-lateral.service
    sudo systemctl daemon-reload
    
    echo "✅ Instancia limpia y purgada."
EOF

echo "📤 SUBIENDO CEREBRO V4.0 SNIPER KING..."
scp -i $KEY LAB_BACKTEST_ANUAL/user_data/strategies/ChacalSniper_Bear44.py $USER@$IP:~/freqtrade/user_data/strategies/
scp -i $KEY LAB_BACKTEST_ANUAL/user_data/strategies/ChacalVolumeHunter_V1.py $USER@$IP:~/freqtrade/user_data/strategies/
scp -i $KEY scripts/Chacal_Trifasico_Control.py $USER@$IP:~/freqtrade/scripts/

echo "🔄 RE-ARMANDO SERVICIOS..."
ssh -i $KEY $USER@$IP << 'EOF'
    sudo systemctl restart chacal-control
    echo "🚀 SISTEMA ELITE EN LÍNEA. +527% ROI ACTIVADO."
EOF
