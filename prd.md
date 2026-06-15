
## 🧬 PharmaTrace AI

**"El agente de IA que detecta medicamentos falsificados antes de que lleguen al paciente."**

---

## El problema en una oración

Cada año, **más de 1 millón de personas mueren** por medicamentos falsificados o subestándar. En 2026, con el auge de fármacos de alto perfil como Ozempic/semaglutida vendiéndose por canales informales, la cadena farmacéutica nunca ha sido más vulnerable — y los sistemas de trazabilidad siguen siendo fragmentados, manuales e incapaces de actuar en tiempo real.

---

## La solución: un Reasoning Agent multicapa

PharmaTrace AI es un agente que **razona en pasos** sobre los datos de la cadena de suministro farmacéutica para:

1. **Verificar autenticidad** → cruza el número de lote, código de barras serializado y ruta de distribución contra el registro inmutable (blockchain como backend)
2. **Detectar anomalías** → identifica patrones sospechosos: lotes que aparecen en dos lugares simultáneamente, proveedores no certificados, rutas geográficas inusuales
3. **Evaluar riesgo** → el agente razona: *"Este lote viene de un proveedor en lista negra de la FDA y cambió de manos 3 veces en 48 horas — riesgo ALTO"*
4. **Generar reporte de compliance** → produce un documento estructurado listo para auditoría regulatoria (DSCSA, FMD)
5. **Alertar a stakeholders** → notifica vía Teams/email a los responsables de calidad

---

## Stack técnico exacto

```txt
Capa de datos:      Fabric IQ (Microsoft Fabric)
                    → lakehouse con historial de lotes, proveedores, eventos
                    → structured data para queries analíticos

Capa de agente:     Foundry IQ (Azure AI Foundry)
                    → Azure AI Agent Service (multi-step reasoning)
                    → GPT-4o como modelo base
                    → grounding con documentos regulatorios (DSCSA, FMD, listas negras FDA/EMA)
                    → tool calls: verificar lote en blockchain, consultar proveedor, 
                      calcular risk score, generar reporte PDF

Capa de notif:      Work IQ (M365)
                    → Teams webhook para alertas críticas
                    → Adaptive Cards para respuesta rápida del equipo

Backend:            Python + FastAPI
Frontend:           Next.js / TypeScript
Blockchain:         Registro inmutable (no lo mencionas como "blockchain" en el pitch,
                    lo llamas "tamper-proof audit ledger")
Dev tools:          GitHub Copilot en VS Code (cumple requisito del hackathon)
```

Los **3 Microsoft IQ layers** están integrados de forma orgánica, no forzada. Eso es clave para los jueces.

---

## El flujo del agente (lo que ves en el demo)

```txt
Usuario ingresa:  → Número de lote + origen + ruta de distribución

Agente, paso 1:   "Verificando autenticidad del lote #MX-2026-4471..."
                  → Consulta el ledger inmutable
                  → Resultado: el lote aparece 2 veces en locaciones distintas ⚠️

Agente, paso 2:   "Analizando proveedor de origen..."
                  → Cruza contra base de proveedores certificados (FDA, EMA)
                  → Resultado: proveedor no certificado en Europa 🔴

Agente, paso 3:   "Evaluando patrón de distribución..."
                  → 3 cambios de manos en 48 horas, ruta inusual China → México → España
                  → Resultado: patrón consistente con cadena de distribución ilícita 🔴

Agente, paso 4:   "Generando reporte de riesgo..."
                  → Risk score: 94/100 (CRÍTICO)
                  → Acciones recomendadas: retiro inmediato, notificación a COFEPRIS/EMA/FDA

Agente, paso 5:   → Alerta enviada a Teams del equipo de calidad
                  → Reporte PDF generado para auditoría regulatoria
```

Eso es lo que muestras en el demo: **razonamiento visible, paso a paso, con evidencia citada**.

---

## Por qué gana en el hackathon

| Criterio del jurado | Cómo lo cumples |
|---|---|
| Creatividad e innovación | Primer agente que combina multi-step reasoning + trazabilidad farmacéutica + compliance regulatorio |
| Excelencia técnica | Reasoning real en pasos, no un chatbot. Tool calls reales. Grounding con documentos regulatorios |
| Impacto real | "Vidas en juego" — el problema más tangible que puedes presentar |
| Integración Microsoft IQ | **3 capas**: Foundry IQ (agente), Fabric IQ (datos), Work IQ (alertas) |
| Demo memorable | Flujo visual con pasos de razonamiento, mapa de ruta, risk score y alerta en vivo |

---

## El nombre del pitch

> **PharmaTrace AI — Drug Traceability & Counterfeit Risk Agent**  
> *"From batch to patient. Every step verified. Every anomaly caught."*

No mencionas blockchain en el headline. Lo mencionas como **"tamper-proof audit ledger"** en el slide técnico si preguntan. El valor del pitch es en idioma enterprise: **trazabilidad, compliance, riesgo, vidas humanas**.

---

## MVP para hacer submit HOY

Lo mínimo que necesitas funcionando para hacer una submission sólida:

- ✅ Un formulario de input (número de lote, proveedor, ruta)
- ✅ Un agente Azure AI con **mínimo 3 pasos de razonamiento visibles** en la UI (streaming)
- ✅ Una base de datos ficticia pero realista de lotes y proveedores en Fabric o JSON
- ✅ Un risk score final con explicación
- ✅ README con arquitectura, instrucciones y qué Microsoft IQ usa
- ✅ Video demo de 2–3 minutos mostrando el flujo completo


--> Usar hyperledger fabric para la blockchain "enterprice"