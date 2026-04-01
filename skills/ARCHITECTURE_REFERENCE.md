# Chacal Zero Friction - Arquitectura de Referencia

## Actualizado: 2026-04-01

---

## ARQUITECTURA DUAL (ESTADO ACTUAL)

| Bot | Entorno | Estrategia | Modo | Horario |
|-----|---------|------------|------|---------|
| **Sniper** | AWS `15.229.158.221` | `ChacalSniper_Bear44` | Dry Run | 24/7 |
| **Volume Hunter** | PC Local | `ChacalVolumeHunter_V1` | En validación | A definir |

---

## CÓMO ACTUALIZAR EL SERVER AWS (FLUJO OFICIAL)

**Paso 1 — Hacés cambios en tu PC y los guardás en Git:**
```
git add .
git commit -m "descripción del cambio"
git push origin master
```

**Paso 2 — Le decís al server que descargue los cambios:**
```
ssh -i skills\llave-sao-paulo.pem ec2-user@15.229.158.221 "cd /home/ec2-user/freqtrade && git pull origin master && docker-compose down && docker-compose up -d"
```

> ⚠️ El server tiene su propia copia de archivos. La llave `.pem` está en `skills/llave-sao-paulo.pem`.
> El git en el server NO estaba configurado inicialmente. Se conectó como repo el 2026-04-01.

---

## REGLAS DE SEGURIDAD (OBLIGATORIAS)

1. **NUNCA subir** archivos de `configs/` — contienen tokens de Telegram y claves de Binance.
2. **Los archivos ignorados** están en `.gitignore` — `CHACAL_VOLUME_HUNTER/user_data/configs/` está bloqueado.
3. **Secrets solo viven en tu PC**, nunca en GitHub.
4. Si GitHub manda alerta de "secret exposed" → hacer `git reset --hard <commit_anterior>` + `git push --force`.

---

## REFERENCIA RÁPIDA DE ARCHIVOS

| Archivo | Propósito |
|---------|-----------|
| `PROJECT_SNIPER_AWS/user_data/strategies/ChacalSniper_Bear44.py` | Estrategia Bear para AWS |
| `CHACAL_VOLUME_HUNTER/user_data/strategies/ChacalVolumeHunter_V1.py` | Estrategia Volume para PC |
| `CHACAL_VOLUME_HUNTER/user_data/configs/config_volume.json` | Config local PC (NO subir a Git) |
| `PROJECT_SNIPER_AWS/docker-compose.aws.yml` | Template del compose de AWS |
| `skills/llave-sao-paulo.pem` | Llave SSH del server AWS |
| `skills/ROADMAP_SNIPER.md` | Historial de resultados y ADN del Sniper |

---

## CUÁNDO APLICA CADA ACCIÓN

- **Cambio en estrategia Sniper** → Editar `.py` → `git push` → `ssh + git pull + docker restart` en AWS.
- **Cambio en estrategia Volume** → Editar `.py` local → Backtest/Hyperopt → luego deploy.
- **El server se cae** → `ssh → docker-compose up -d`
- **Actualizar config del server** → `scp` del archivo local al server (los configs NO van a Git).