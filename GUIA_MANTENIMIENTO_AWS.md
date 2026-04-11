# 🛡️ GUIA DE MANTENIMIENTO: AWS NATIVO (TRIFÁSICO)

Esta guía contiene los procedimientos para monitorear y auditar el Fondo Trifásico Chacal en la instancia de AWS São Paulo.

## 🛰️ CONEXIÓN RÁPIDA

```bash
ssh -i skills/llave-sao-paulo.pem ubuntu@54.94.193.76
```

---

## 🚦 MONITOREO DE SERVICIOS

El sistema usa `systemd`. Puedes gestionar los procesos con estos comandos:

| Servicio | Función | Comando de Estado |
| :--- | :--- | :--- |
| **Orquestador** | Cerebro (Cambio 3.9%) | `systemctl status chacal-control` |
| **Lateral Bot** | Especialista Rango | `systemctl status ft-lateral` |
| **Bear Bot** | Especialista Dumps | `systemctl status ft-bear` |
| **Bull Bot** | Especialista Pumps | `systemctl status ft-bull` |

---

## 🪵 GESTIÓN DE LOGS (AUDITORÍA)

Usa `journalctl` para ver qué está pasando en tiempo real:

- **Efecto Matrix (Ver todo en vivo):**
  `journalctl -u ft-lateral -u ft-bear -u ft-bull -u chacal-control -f`
- **Ver solo el cambio de régimen:**
  `journalctl -u chacal-control -f`
- **Buscar errores críticos:**
  `journalctl -p 3 -xb`

---

## 🧠 SALUD DEL SERVIDOR (RECURSOS)
- **RAM y Swap:** `free -h`
- **Carga de CPU:** `htop` (o `top`)
- **Espacio en Disco:** `df -h`

---

## 🛡️ PROTOCOLO DE CONCURRENCIA
**REGLA DE ORO:** Solo DEBEN estar activos dos servicios:
1. `chacal-control.service` (Siempre)
2. **UNO** de los tres bots (`ft-lateral`, `ft-bear` o `ft-bull`).

Si ves que hay dos bots encendidos al mismo tiempo, reinicia el cerebro:
`sudo systemctl restart chacal-control`

---

## 🏁 CONTINGENCIAS
- **El bot no responde en Telegram:** Reinicia el servicio activo (ej. `sudo systemctl restart ft-lateral`).
- **El servidor se reinicia:** No hagas nada. Los servicios están en `enabled` y arrancarán solos.
- **Cambio de API Keys:** Edita `/home/ubuntu/chacal/user_data/configs/config.json` y reinicia el bot activo.

---
*Fondo Trifásico: Resiliencia Blindada.*
