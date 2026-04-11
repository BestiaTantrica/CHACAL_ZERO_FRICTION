# 🧪 PROTOCOLO DE ESTUDIO - CHACAL LATERAL V4
**Hilo de Referencia:** a0f84cb3-c7db-475c-95bf-c2c7495384b3

## 🎯 REGLAS DE ORO PARA EL ESTUDIO
1. **Prioridad del TARGET_MID:** Cualquier cambio en el RSI o Scoring no debe comprometer la salida de Banda Media.
2. **Validación Multi-Régimen:** Todo ajuste debe probarse en Mayo 24 (Lateral), Septiembre 24 (Bull) y Junio 24 (Bear).
3. **Apalancamiento x5:** No subir a x10 hasta que el Drawdown en meses bajistas sea < 15%.

## 📊 ESTADO DEL "RSI FINO" (1m)
- **Estado Actual:** NO OPTIMIZADO mediante Hyperopt. Se están usando valores institucionales estándar (30/70).
- **Lógica de Integración:** El RSI 1m no es un gatillo binario, sino un componente del **Scoring Cuántico**.
- **Pendiente:** Ejecutar `freqtrade hyperopt` específicamente para los parámetros `rsi_long_max` y `rsi_short_min` dentro del espacio de la V4.

## ⚖️ REVALIDACIÓN POR MERCADOS
| Régimen | Periodo | Resultado V4 | Veredicto |
|---------|---------|--------------|-----------|
| **LATERAL** | Mayo 2024 | **+12.8%** | ✅ Óptimo (15 trades/día) |
| **BULL LENTO** | Sept 2024 | **+7.9%** | ✅ Seguro (Resiliente) |
| **BEAR/BREAKOUT** | Junio 2024 | **DD -10%** | ⚠️ Protegido por MACRO_BREAKOUT |

## 🚀 PRÓXIMOS ESTUDIOS (BACKLOG)
- [ ] **Hyperopt de 1m:** Encontrar los umbrales de agotamiento RSI que maximicen el WinRate en lugar del profit total.
- [ ] **Ajuste de Salida Airbag:** Probar si bajar el Airbag de -3.5% a -4.5% mejora el profit en Septiembre dándole más aire a los Longs.
- [ ] **Script de Delegación (MANDO):** Definir el disparador automático que apague "Lateral" y encienda "Sniper Bear" basado en la variable `is_lateral`.
