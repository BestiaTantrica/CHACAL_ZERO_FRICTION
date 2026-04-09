# PROTOCOLO DE MEMORIA LIVIANA Y DOCUMENTACIÓN

Este protocolo define cómo deben los agentes (IAs) gestionar los descubrimientos técnicos y el estado del repositorio para preservar el contexto (ahorrar tokens) y mantener la sanidad del repositorio.

## 1. Regla de Saneamiento Documental
Cada hallazgo o apunte debe caer obligatoriamente en UNA de estas tres categorías:

1. **ESTADO** -> Va a `CHACAL_MASTER_ESTADO.md`
   - Tablero táctico, 1 página máximo.
   - Solo listas, semáforos, bloqueos activos y próximos pasos inmediatos.
   - **Prohibido:** Logs largos, autopsias, historias o código en este archivo.

2. **EVIDENCIA (Auditoría)** -> Va a `AUDITORIA_[TEMA].md`
   - Documentos de análisis forense (ej: `AUDITORIA_BEAR44.md`).
   - Sirve para archivar hipótesis, comandos de backtest exactos, resultados y la decisión final concluyente.
   - A leer sólo si la IA o el usuario necesitan entender de dónde vino una decisión.

3. **DECISIÓN (Manual Operativo)** -> Va a `INSTRUCCIONES_CLINE_[PROYECTO].md`
   - El "Cómo se opera esto".
   - Comandos actualizados, variables de configuración, reglas activas y resumen de "estado de replicación histórica".

## 2. Formato Mínimo para Hallazgos en Evidencias
Al escribir una Auditoría/Evidencia, utilizar esta estructura rápida:
- **Fecha:** YYYY-MM-DD
- **Hipótesis:** ¿Qué pensábamos que pasaría / por qué lo probamos?
- **Fuente / Comando:** ¿Qué ejecutamos o de qué log viene?
- **Resultado:** Porcentajes, trades, error literal, etc.
- **Decisión / Conclusión:** ¿Confirmado o refutado? ¿Qué cambia en nuestro plan?

*Implementando este protocolo garantizamos que las transiciones entre agentes sean "Zero Friction".*
