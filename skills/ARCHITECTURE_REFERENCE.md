# Chacal Zero Friction - Referencia General

> **Última actualización:** 2026-04-02
> **Nota:** Cada proyecto tiene su propio maestro. Este archivo es solo referencia general compartida.

---

## ARQUITECTURA DUAL

| Bot | Proyecto | Entorno | Estrategia | Modo | Maestro |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Sniper Bear** | `PROJECT_SNIPER_AWS/` | AWS `54.94.193.76` (servidor) | `ChacalSniper_Bear44` | SHORT (Bear) | `PROJECT_SNIPER_AWS/INSTRUCCIONES_CLINE_BEAR.md` |
| **Volume Hunter** | `CHACAL_VOLUME_HUNTER/` | **PC Local** (tu máquina) | `ChacalVolumeHunter_V1` | LONG (Bull/Lateral) | `CHACAL_VOLUME_HUNTER/INSTRUCCIONES_CLINE_VOLUME.md` |

---

## ESTRUCTURA DEL REPOSITORIO

```text
CHACAL_ZERO_FRICTION/
├── CHACAL_VOLUME_HUNTER/          ← Proyecto Volume Hunter (PC)
│   ├── INSTRUCCIONES_CLINE_VOLUME.md  ← MAESTRO Volume Hunter
│   ├── docker-compose.yml
│   ├── check_market_trend.py
│   └── user_data/
├── PROJECT_SNIPER_AWS/            ← Proyecto Sniper Bear (AWS)
│   ├── INSTRUCCIONES_CLINE_BEAR.md    ← MAESTRO Sniper Bear
│   ├── docker-compose.yml
│   └── user_data/
├── strategies/                    ← Estrategias compartidas
│   ├── ChacalVolumeHunter_V1.py
│   ├── ChacalVolumeHunter_V1.json
│   └── ChacalSniper_Bear44.py
├── skills/                        ← Utilidades generales
│   ├── ARCHITECTURE_REFERENCE.md  ← Este archivo
│   ├── analyze_aws_trades.py
│   └── llave-sao-paulo.pem
└── mcp-server-nodejs/             ← Servidor MCP
```

---

## SERVIDOR AWS

| Parámetro | Valor |
| :--- | :--- |
| IP | `54.94.193.76` |
| Usuario | `ubuntu` |
| Llave SSH | `skills/llave-sao-paulo.pem` |
| Path Freqtrade | `/home/ec2-user/freqtrade` |

### Cómo Actualizar el Server

```bash
# 1. Commit + push desde PC
git add .
git commit -m "descripción"
git push origin master

# 2. Pull + restart en server
ssh -i skills\llave-sao-paulo.pem ubuntu@54.94.193.76 \
  "cd /home/ec2-user/freqtrade && git pull origin master && docker-compose down && docker-compose up -d"
```

---

## REGLAS DE SEGURIDAD

1. ❌ **NUNCA subir** `*/user_data/configs/` a Git (tokens, claves)
2. ❌ **NUNCA subir** `skills/llave-sao-paulo.pem` a Git
3. ✅ `.gitignore` bloquea estas carpetas
4. ✅ Secrets solo viven en PC local y servidor

---

## MCP SERVER (CHACAL-ZERO-FRICTION)

Herramientas MCP disponibles:

- `freqtrade_control` - Control del bot (status, profit, daily, balance)
- `docker_freqtrade` - Comandos Docker (backtesting, hyperopt, list-data)
- `crypto_market_intel` - Datos de mercado Binance (ticker, OHLCV)
- `risk_manager` - Gestión de riesgo (Kelly, correlación, volatilidad)
- `groq_intel_analysis` - Análisis IA con Groq
- `aws_ssh_control` - Ejecutar SSH/SCP en AWS

---

## PARA LEER ANTES DE TRABAJAR

| Si trabajas en... | Lee este archivo |
| :--- | :--- |
| Volume Hunter (Bull/Long) | `CHACAL_VOLUME_HUNTER/INSTRUCCIONES_CLINE_VOLUME.md` |
| Sniper Bear (Short) | `PROJECT_SNIPER_AWS/INSTRUCCIONES_CLINE_BEAR.md` |
| Arquitectura general | Este archivo |