scp -i skills\llave-sao-paulo.pem -o StrictHostKeyChecking=no config_v5_oracle.json ubuntu@129.80.104.116:/home/ubuntu/CHACAL_LATERAL_AWS/config.json
scp -i skills\llave-sao-paulo.pem -o StrictHostKeyChecking=no strategies\ChacalLateral_V5.py ubuntu@129.80.104.116:/home/ubuntu/CHACAL_LATERAL_AWS/user_data/strategies/
ssh -i skills\llave-sao-paulo.pem -o StrictHostKeyChecking=no ubuntu@129.80.104.116 "sudo systemctl restart ft-lateral"
write-host "[✅] Deploy Completado"
