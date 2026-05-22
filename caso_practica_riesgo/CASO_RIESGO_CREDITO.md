# 🎯 CASO DE PRÁCTICA DE RIESGO DE CRÉDITO: "Banco Solución Financiera"

## 1. Contexo de Negocio
El **Banco Solución Financiera** es una institución líder en el segmento de banca minorista. Uno de sus productos más rentables, pero a la vez de mayor riesgo, es el **Préstamo de Efectivo Consumo** (préstamos de libre disponibilidad a mediano plazo).

En el último año, el banco ha experimentado un incremento del **15% en su cartera vencida**, lo cual ha afectado sus provisiones ante el regulador financiero (SBS) y ha reducido la rentabilidad anual del banco en un **8%**. 

La gerencia de Riesgos Minoristas ha decidido reemplazar la política actual de evaluación de créditos (basada en reglas manuales y corte simple de puntaje de central) por un **modelo predictivo de Machine Learning** altamente preciso que clasifique la probabilidad de que un solicitante incurra en impago (Default) en los siguientes 12 meses.

---

## 2. Definición del Problema Técnico
El objetivo es construir un pipeline completo que identifique si un cliente incurrirá en impago de su préstamo:
*   **Variable Objetivo (Target):** `DEFAULT` (0 = Cliente al día / paga a tiempo; 1 = Cliente entra en default / 90+ días de atraso acumulados).
*   **Tipo de Problema:** Clasificación Binaria altamente desbalanceada.
*   **Dataset de Entrenamiento (`clientes_entrenamiento.csv`):** Contiene 15,000 registros históricos con variables sociodemográficas, financieras y de comportamiento crediticio, incluyendo el target real.
*   **Dataset de Prueba (`clientes_prueba.csv`):** Contiene 5,000 registros de nuevos solicitantes durante el primer trimestre de 2026. **No cuenta con la columna `DEFAULT`**. El equipo debe predecir sus probabilidades y generar un archivo de entrega (`submission.csv`).

---

## 3. Diccionario de Datos

| Nombre de Variable | Tipo de Dato | Descripción |
|---|---|---|
| `ID_CLIENTE` | Alfanumérico (ID) | Identificador único del cliente. |
| `FECHA_SOLICITUD` | Fecha (YYYY-MM-DD) | Fecha en la que el cliente solicitó el préstamo. |
| `EDAD` | Numérico (Entero) | Edad del cliente al momento de la solicitud. *(¡Atención con datos ruidosos!)*. |
| `ESTADO_CIVIL` | Categórico | SOLTERO, CASADO, DIVORCIADO. |
| `NIVEL_EDUCATIVO` | Categórico | SECUNDARIA, UNIVERSITARIO, POSGRADO. |
| `SITUACION_LABORAL` | Categórico | DEPENDIENTE, INDEPENDIENTE, DESEMPLEADO. |
| `TIPO_VIVIENDA` | Categórico | ALQUILER, PROPIA, HIPOTECA. |
| `INGRESOS_MENSUALES` | Numérico (Float) | Ingreso neto mensual declarado por el cliente. *(¡Contiene datos faltantes y outliers extremos!)*. |
| `LINEA_CREDITO_TOTAL` | Numérico (Float) | Límite total de crédito aprobado para el cliente en el sistema financiero. |
| `SALDO_DEUDOR_TOTAL` | Numérico (Float) | Deuda total acumulada del cliente en el sistema financiero al solicitar el crédito. |
| `NUM_ATRASOS_30_59_DIAS` | Numérico (Entero) | Veces que el cliente se atrasó entre 30 y 59 días en los últimos 2 años. |
| `NUM_ATRASOS_60_89_DIAS` | Numérico (Entero) | Veces que el cliente se atrasó entre 60 y 89 días en los últimos 2 años. |
| `NUM_ATRASOS_90_MAS_DIAS` | Numérico (Entero) | Veces que el cliente se atrasó 90 días o más en los últimos 2 años. |
| `NUM_CONSULTAS_CENTRAL` | Numérico (Entero) | Número de búsquedas de su reporte en la central de riesgo en los últimos 6 meses. |
| `DEFAULT` | Numérico (Binario) | **Variable objetivo.** 1 = Default / 0 = No Default. *(Solo en el dataset de entrenamiento)*. |

---

## 4. Matriz de Impacto Financiero (Métricas de Negocio)
La Financista de tu equipo liderará este análisis, pero el modelo debe programarse para optimizar el **Retorno de Inversión (ROI) Neto** basado en el umbral probabilístico de riesgo. El banco ha calculado los siguientes costos promedios por cada crédito evaluado:

| Condición Real | Decisión del Modelo (Aprobar: Score < Umbral) | Decisión del Modelo (Rechazar: Score >= Umbral) | Explicación del Negocio |
|---|---|---|---|
| **PAGADOR REAL** (`DEFAULT = 0`) | **ÉXITO (Verdadero Negativo)**<br>Ganancia Neta: **+\$450 USD** | **COSTO DE OPORTUNIDAD (Falso Positivo)**<br>Pérdida Neta: **-\$150 USD** | Si apruebas a un pagador, ganas intereses. Si lo rechazas, pierdes al cliente ante la competencia (costo de adquisición perdido). |
| **DEFAULTER REAL** (`DEFAULT = 1`) | **PÉRDIDA CAPITAL (Falso Negativo)**<br>Pérdida Neta: **-\$3,000 USD** | **PÉRDIDA EVITADA (Verdadero Positivo)**<br>Ganancia Neta: **\$0 USD** | Si apruebas a alguien que no pagará, pierdes el capital promedio prestado. Si lo rechazas, evitas la pérdida (el impacto neto es neutro). |

### Fórmula de ROI Financiero Neto del Modelo:
$$\text{ROI Neto} = (VN \times 450) - (FP \times 150) - (FN \times 3000)$$

*El objetivo del equipo es encontrar un modelo y un umbral de decisión que MAXIMICEN esta cifra en el conjunto de validación.*

---

## 5. Entregables del Equipo
El jurado evaluará la solución bajo la misma estructura del plan maestro:

1.  **Fase 0 (Orquestador):** Archivo `case_config.json` inicial generado y supuestos de negocio documentados en las diapositivas.
2.  **Fase 1 (EDA):** Reporte de calidad de datos, limpieza de outliers/anomalías de edad e ingresos, y la matriz de correlaciones en Dark Mode.
3.  **Fase 2 (Modelado):** Pipeline reproducible con imputadores y encoders ajustados *solo* sobre train, curvas de evaluación (ROC, PR, Confusión) y optimización de umbral por ROI financiero.
4.  **Inferencia y Submission:** Un archivo `submission.csv` con las columnas:
    *   `ID_CLIENTE`
    *   `PROB_DEFAULT` (probabilidad continua generada por el modelo, ej. 0.185)
    *   `DECISION_APROBADO` (1 = Aprobado / 0 = Rechazado; basado en el umbral optimizado de ROI).
5.  **Exposición (Slides):** Defensa de la solución liderada por el bloque de negocio (Financista y Ambiental), explicando cómo el modelo mejora la rentabilidad en comparación con la política de aprobar a todos.
