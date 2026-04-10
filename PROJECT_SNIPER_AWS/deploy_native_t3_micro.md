# 🦅 CHACAL HÍBRIDO NATIVO — DESPLIEGUE t3.micro SIN DOCKER

> **Protocolo:** PEGASO 3.3 — Despliegue híbrido nativo
> **Target:** `ubuntu@15.229.158.221`
> **Instancia:** `chacal-hibrido-nativo` (`t3.micro`, 1 GB RAM)
> **Objetivo:** correr Freqtrade en modo nativo con `systemd`, swap obligatorio y consumo mínimo de RAM.

---

## 0. Decisiones operativas cerradas

1. **Docker queda prohibido** en esta instancia. En 1 GB RAM el overhead mata margen operativo.
2. **Swap 4 GB es obligatorio** antes de instalar Freqtrade.
3. **Un servicio por estrategia** vía `systemd`.
4. **No levantar Bear + Volume al mismo tiempo** hasta validar consumo real. En `t3.micro`, primero se estabiliza **Bear** y luego se decide si Volume entra como servicio alterno o programado.
5. **Los configs live no van a Git**. Se suben con `scp` después del deploy base.

---

## 1. Pre-chequeo mínimo antes de tocar AWS

Checklist mental PEGASO:

- Proyecto actual: **Despliegue híbrido nativo AWS**
- Estado AWS actual: **pendiente de verificación manual**
- Pendiente crítico heredado: **mantener RAM < 80% y evitar OOM**
- Git remoto: repo oficial `BestiaTantrica/CHACAL_ZERO_FRICTION`
- Objetivo de esta sesión: **dejar listo el playbook nativo + servicios systemd**

---

## 2. Preparación del búnker

### 2.1 Conexión SSH

```cmd
ssh -i skills\llave-sao-paulo.pem ubuntu@15.229.158.221
```

### 2.2 Crear swap de 4 GB

```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h
swapon --show
```

**Criterio de éxito:** `free -h` debe mostrar swap activa antes de seguir.

---

## 3. Dependencias base del sistema

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv python3-dev build-essential \
  libssl-dev libffi-dev git curl wget pkg-config logrotate
```

---

## 4. TA-Lib nativo sin saltar errores

```bash
cd /tmp
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib
./configure --prefix=/usr
make
sudo make install
```

```bash
cd ..
rm -rf /tmp/ta-lib /tmp/ta-lib-0.4.0-src.tar.gz
```

### Verificación rápida

```bash
ldconfig -p | grep ta-lib
```

Si esto falla, **parar**. No seguir a Freqtrade con TA-Lib roto.

---

## 4.1 Chequeo de memoria obligatorio antes de arrancar servicios

```bash
free -h
swapon --show
```

**Regla PEGASO:** si la RAM queda por encima de **80%** sostenido o el swap empieza a crecer violentamente apenas arranca Bear, no habilitar Volume en esta instancia.

---

## 5. Clonación limpia del repo y venv

```bash
cd /home/ubuntu
git clone https://github.com/BestiaTantrica/CHACAL_ZERO_FRICTION.git chacal
cd /home/ubuntu/chacal
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel setuptools
pip install -e .
freqtrade --version
```

> Si `pip install -e .` falla porque el repo no es instalable como paquete, usar plan B:

```bash
source /home/ubuntu/chacal/.venv/bin/activate
pip install freqtrade
```

---

## 6. Estructura operativa recomendada en servidor

```text
/home/ubuntu/chacal/
├── .venv/
├── PROJECT_SNIPER_AWS/
│   └── user_data/
│       ├── configs/
│       │   ├── config_live.json         ← subir manualmente
│       │   └── config_backtest.json
│       └── strategies/
├── CHACAL_VOLUME_HUNTER/
│   └── user_data/
│       ├── configs/
│       │   ├── config_volume.json       ← subir/revisar manualmente
│       │   └── config_backtest.json
└── strategies/
    └── ChacalVolumeHunter_V1.py
```

---

## 7. Subida de configs live y secretos

### 7.1 Bear live

El servicio nativo Bear necesita un config live dedicado. En este repo no aparece versionado, así que hay que subirlo manualmente.

```cmd
scp -i skills\llave-sao-paulo.pem PROJECT_SNIPER_AWS\user_data\configs\config_live.json ubuntu@15.229.158.221:/home/ubuntu/chacal/PROJECT_SNIPER_AWS/user_data/configs/
```

### 7.2 Volume live

Ya existe un `config_volume.json`, pero contiene credenciales/versionado local. Revisarlo antes de usarlo en AWS.

```cmd
scp -i skills\llave-sao-paulo.pem CHACAL_VOLUME_HUNTER\user_data\configs\config_volume.json ubuntu@15.229.158.221:/home/ubuntu/chacal/CHACAL_VOLUME_HUNTER/user_data/configs/
```

### 7.3 Regla de seguridad

- Validar API keys reales en servidor
- Mantener `api_server.listen_ip_address = 127.0.0.1`
- No exponer puertos públicos

---

## 8. Servicio systemd — Bear

Crear `/etc/systemd/system/chacal-bear.service`:

```ini
[Unit]
Description=Freqtrade Chacal Sniper Bear (Native)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/chacal
Environment="PATH=/home/ubuntu/chacal/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/home/ubuntu/chacal/.venv/bin/freqtrade trade --config /home/ubuntu/chacal/PROJECT_SNIPER_AWS/user_data/configs/config_live.json --strategy ChacalSniper_Bear_ULTRA --strategy-path /home/ubuntu/chacal/PROJECT_SNIPER_AWS/user_data/strategies
Restart=always
RestartSec=10
KillSignal=SIGINT
TimeoutStopSec=60

[Install]
WantedBy=multi-user.target
```

### Activación

```bash
sudo systemctl daemon-reload
sudo systemctl enable chacal-bear
sudo systemctl start chacal-bear
sudo systemctl status chacal-bear --no-pager
```

---

## 9. Servicio systemd — Volume

Crear `/etc/systemd/system/chacal-volume.service`:

```ini
[Unit]
Description=Freqtrade Chacal Volume Hunter (Native)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/chacal
Environment="PATH=/home/ubuntu/chacal/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/home/ubuntu/chacal/.venv/bin/freqtrade trade --config /home/ubuntu/chacal/CHACAL_VOLUME_HUNTER/user_data/configs/config_volume.json --strategy ChacalVolumeHunter_V1 --strategy-path /home/ubuntu/chacal/strategies
Restart=always
RestartSec=10
KillSignal=SIGINT
TimeoutStopSec=60

[Install]
WantedBy=multi-user.target
```

### Activación controlada

```bash
sudo systemctl daemon-reload
sudo systemctl enable chacal-volume
```

> **Recomendación PEGASO:** no hacer `start` de `chacal-volume` hasta medir RAM real con Bear activo.

---

## 10. Logs rotativos y monitoreo liviano

### 10.1 journalctl en vivo

```bash
journalctl -u chacal-bear -f
journalctl -u chacal-volume -f
```

### 10.2 Persistencia acotada de journald

Crear override liviano:

```bash
sudo mkdir -p /etc/systemd/journald.conf.d
sudo tee /etc/systemd/journald.conf.d/chacal-limit.conf >/dev/null <<'EOF'
[Journal]
SystemMaxUse=200M
SystemMaxFileSize=20M
MaxRetentionSec=7day
EOF
sudo systemctl restart systemd-journald
```

### 10.2.b Rotación explícita y limpieza de journals

```bash
sudo journalctl --rotate
sudo journalctl --vacuum-time=7d
sudo journalctl --vacuum-size=200M
```

### 10.3 Verificación de RAM

```bash
free -h
ps aux --sort=-%mem | head
```

**Regla dura:** si RAM usada + cache útil deja menos de ~200 MB libres y el swap empieza a crecer agresivamente, no correr ambos bots simultáneos.

---

## 11. Operación diaria mínima

### Estado de servicios

```bash
systemctl status chacal-bear --no-pager
systemctl status chacal-volume --no-pager
```

### Reinicio manual

```bash
sudo systemctl restart chacal-bear
sudo systemctl restart chacal-volume
```

### Ver consumo

```bash
free -h
top
```

### Dashboard remoto solo con túnel SSH

```cmd
ssh -i skills\llave-sao-paulo.pem -L 8081:127.0.0.1:8081 ubuntu@15.229.158.221
```

---

## 12. Contingencias críticas

### Freqtrade no arranca

```bash
sudo journalctl -u chacal-bear -n 80 --no-pager
sudo journalctl -u chacal-volume -n 80 --no-pager
```

### TA-Lib rota

- Repetir compilación nativa
- Confirmar `ldconfig -p | grep ta-lib`
- Reinstalar wheels dentro del venv

### RAM > 80%

```bash
free -h
sudo systemctl stop chacal-volume
```

Prioridad de supervivencia: **Bear primero**.

### API y dashboard

- Mantener la API en `127.0.0.1`.
- Entrar al dashboard solo con túnel SSH.
- No abrir `8081` al mundo en Security Groups.

---

## 13. Veredicto operativo

Para una `t3.micro`, el modo correcto es:

- **Freqtrade nativo**
- **Swap 4 GB**
- **systemd**
- **journalctl en vez de logs gigantes**
- **Bear como servicio primario**
- **Volume solo si la RAM real lo permite**

Si querés operación dual permanente, la arquitectura aconsejable ya pasa a `t3.small` o separar bots por instancia.