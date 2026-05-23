# Guia Aplicada de Riesgo Crediticio para Datathon Bancaria

## Objetivo del documento

Servir como guia practica de ejecucion para resolver un caso de scoring de credito en Datathon. Integra lo mas util de los documentos de `docs/` y lo convierte en acciones concretas para EDA, feature engineering, modelamiento, validacion, interpretabilidad, ROI y presentacion.

## Fuentes revisadas

Se revisaron 61 PDFs en `docs/`. No hubo archivos ilegibles; algunos PDFs tienen extraccion de texto ruidosa por codificacion interna, pero se recupero contenido suficiente para clasificar y extraer ideas aplicables.

Fuentes principales usadas para esta guia:

- `RCO 2 - Análisis del Scoring de Crédito 2026.pdf`
- `RCO 3 Análisis variables que afecta la mora 2026.pdf`
- `RCO 4 - Modelos de pérdida esperada 2026.pdf`
- `RCO 5 - Modelos de incumplimiento Logit 2026.pdf`
- `S4 El Nuevo Acuerdo de Basilea para Riesgo de Crédito.pdf`
- `S5 Modelo de Credit Scoring - Salvador Rayo.pdf`
- `S6 Gestión de Riesgo y arboles decision.pdf`
- `S7 Redes Neuronales y Evaluación de Créditos Financieros.pdf`
- `Credit Risk Modeling using Excel and VBA-Wiley - Wiley (2007).pdf`
- `Paper Loan repayment behavior among the clients of Indian microfinance.pdf`
- `SISTEMA DE MONITOREO PERLAS.pdf`
- `9. Reg. de Requerimiento de Patrimonio Efectivo por Riesgo de Crédito_Res. SBS N° 14354-2009.pdf`
- `RCO 1 Crisis financiera.pdf`

## Principio rector para ganar

El reto no se gana solo con el modelo de mayor AUC. Se gana con una solucion que:

1. Predice `default_90d` sin leakage.
2. Ordena bien el riesgo.
3. Entrega probabilidades razonablemente calibradas.
4. Convierte el score en politica bancaria de 3 bandas.
5. Mide impacto financiero.
6. Explica las variables en lenguaje de negocio.

Referencias internas: `Credit Risk Modeling using Excel and VBA-Wiley - Wiley (2007).pdf`, `RCO 4 - Modelos de pérdida esperada 2026.pdf`, `S5 Modelo de Credit Scoring - Salvador Rayo.pdf`.

## Flujo recomendado para 3 horas

| Tiempo | Fase | Resultado minimo |
|---|---|---|
| 0-10 min | Entender caso y archivos | Target, ID, train/test, metrica, submission |
| 10-35 min | EDA express | Tasa default, nulos, outliers, leakage, variables clave |
| 35-60 min | Feature engineering | Ratios seguros, missing flags, score/mora features |
| 60-105 min | Modelos | Dummy, Logit, Random Forest/HGB, boosting si disponible |
| 105-130 min | Validacion | AUC, Gini, KS, Brier, Lift, overfitting |
| 130-150 min | ROI y bandas | Threshold, politica bajo/medio/alto |
| 150-170 min | Submission e interpretabilidad | CSV, feature importance/SHAP |
| 170-180 min | Storytelling y revision | Slides, supuestos, mensajes clave |

Recomendacion aplicada al caso: si algo falla, sacrificar tuning y redes neuronales antes que submission, anti-leakage, ROI o explicabilidad.

## Conceptos clave que deben aparecer en la solucion

### PD, LGD, EAD y perdida esperada

Aunque la data solo permita estimar `PD`, el marco correcto es:

```text
Perdida esperada = PD x EAD x LGD
```

Fuente interna: `RCO 4 - Modelos de pérdida esperada 2026.pdf`, `S4 El Nuevo Acuerdo de Basilea para Riesgo de Crédito.pdf`.

Aplicacion:

- `prob_default` aproxima PD.
- El costo de default aprobado aproxima LGD/EAD combinados si el caso da una perdida fija.
- La politica de bandas debe reducir perdida esperada sin destruir demasiado la originacion.

### Score crediticio

Un score ordena clientes por riesgo y sirve para tomar decisiones. La probabilidad no debe quedarse en tabla tecnica.

Fuente interna: `RCO 2 - Análisis del Scoring de Crédito 2026.pdf`, `S5 Modelo de Credit Scoring - Salvador Rayo.pdf`.

Aplicacion:

- Bajo riesgo: aprobar.
- Riesgo medio: condicionar.
- Alto riesgo: rechazar/prevenir.

### Ciclos economicos y estabilidad

El riesgo de credito cambia con desempleo, inflacion, tasas, crisis y condiciones de liquidez.

Fuente interna: `RCO 1 Crisis financiera.pdf`.

Aplicacion:

- Si hay fecha/periodo, usar split temporal o validar performance por cohorte.
- Si no hay fecha, declarar la limitacion y proponer monitoreo de drift.

## EDA: que hacer y por que

### 1. Target y balance

Acciones:

- Confirmar que `default_90d` sea binario.
- Reportar tasa de default.
- Revisar si hay clases muy desbalanceadas.

Por que importa:

- Define estrategia de metricas y pesos de clase.

Referencia: `RCO 5 - Modelos de incumplimiento Logit 2026.pdf`.

### 2. Nulos como senal

Acciones:

- Para cada variable, calcular `% nulos` y default rate entre nulos vs no nulos.
- Crear flags de missing cuando el nulo tenga significado de negocio.

Variables prioritarias:

- `score_buro`: nulo puede significar sin historial.
- `dias_mora_prev`: nulo puede significar sin mora previa.
- `ingreso_mensual`: nulo puede indicar informalidad o falta de documentacion.

Referencia: `S5 Modelo de Credit Scoring - Salvador Rayo.pdf`, `Paper Loan repayment behavior among the clients of Indian microfinance.pdf`.

### 3. Capacidad de pago y endeudamiento

Acciones:

- Analizar ingreso, deuda, ratio endeudamiento y saldos.
- Crear ratios seguros con pisos para denominadores.
- Usar caps o log para ratios extremos.

Features recomendadas:

```text
ingreso_missing
ingreso_mensual_safe
ratio_deuda_ingreso
ratio_deuda_ingreso_cap
log_ratio_deuda_ingreso
ratio_endeudamiento_cap
flag_endeudamiento_alto
capacidad_pago_neta
```

Referencia: `RCO 3 Análisis variables que afecta la mora 2026.pdf`.

### 4. Historial de pago

Acciones:

- Analizar mora previa, atrasos, score buro y consultas externas.
- Verificar que no sean variables post-evento.
- Crear flags de sin historial y severidad.

Features recomendadas:

```text
buro_sin_historial
score_buro_corregido
sin_mora_previa
dias_mora_max_corregida
mora_score_interact
```

Referencia: `S5 Modelo de Credit Scoring - Salvador Rayo.pdf`, `RCO 3 Análisis variables que afecta la mora 2026.pdf`.

### 5. Segmentacion exploratoria

Segmentos que deben revisarse:

- Region/zona geografica.
- Canal de captacion.
- Tipo de empleo.
- Bandas de ingreso.
- Bandas de endeudamiento.
- Bandas de score buro.

Referencia: `Paper Loan repayment behavior among the clients of Indian microfinance.pdf`, `Emerald Banca móvil un concepto de moda o un canal institucionalizado en la banca minorista del futuro (1).pdf`.

### 6. Leakage

Variables sospechosas:

- Mora posterior al periodo de originacion.
- Estado final del credito.
- Gestion de cobranza posterior.
- Reestructuracion posterior al default.
- Pagos realizados despues del evento.
- Variables calculadas usando test o todo el dataset.

Recomendacion aplicada al caso: si una variable tiene AUC individual extremadamente alto, correlacion demasiado fuerte con target o nombre post-evento, revisarla manualmente.

## Feature engineering prioritario

| Prioridad | Feature | Motivo | Fuente |
|---|---|---|---|
| Alta | `buro_sin_historial` | Inclusión financiera/no bancarizado | `S5 Modelo de Credit Scoring - Salvador Rayo.pdf` |
| Alta | `ratio_deuda_ingreso_cap` | Apalancamiento robusto | `RCO 3 Análisis variables que afecta la mora 2026.pdf` |
| Alta | `sin_mora_previa` | Historial limpio vs sin dato | `RCO 3 Análisis variables que afecta la mora 2026.pdf` |
| Alta | `capacidad_pago_neta` | Margen economico mensual | Recomendacion aplicada al caso |
| Media | interaccion mora x score buro | Severidad combinada | Recomendacion aplicada al caso |
| Media | bandas de edad/ingreso | No linealidad interpretable | `S5 Modelo de Credit Scoring - Salvador Rayo.pdf` |
| Media | region/canal one-hot | Segmentos de originacion | `Paper Loan repayment behavior...pdf` |
| Baja | target/frequency encoding | Solo dentro de CV y con tiempo | Recomendacion aplicada al caso |

## Modelamiento

### Modelos a probar

Orden recomendado:

1. Dummy baseline.
2. Logistic Regression.
3. Random Forest.
4. HistGradientBoosting o LightGBM.
5. XGBoost/CatBoost si estan disponibles.
6. Red neuronal solo si sobra tiempo.

Referencias internas:

- Logit: `RCO 5 - Modelos de incumplimiento Logit 2026.pdf`.
- Arboles: `S6 Gestión de Riesgo y arboles decision.pdf`.
- Redes: `S7 Redes Neuronales y Evaluación de Créditos Financieros.pdf`.

### Tratamiento de desbalance

Recomendacion aplicada al caso:

- Primero usar `class_weight='balanced'` o `scale_pos_weight`.
- No usar SMOTE antes de tener baseline fuerte.
- Si se usa SMOTE, debe estar dentro de pipeline y solo sobre train.
- Recordar que oversampling puede dañar calibracion de probabilidades.

### Validacion

Reglas:

- `stratified_split` por defecto.
- `temporal_split` solo si existe fecha/periodo confiable.
- `group_split` si hay clientes repetidos.
- Nunca ajustar imputadores, encoders ni escaladores antes del split.

Referencia: `Credit Risk Modeling using Excel and VBA-Wiley - Wiley (2007).pdf`.

### Calibracion

Acciones:

- Calcular Brier Score.
- Graficar curva de calibracion.
- Probar calibracion sigmoid si mejora Brier sin perder mucho AUC.

Por que importa:

- La politica de aprobacion usa `prob_default`; si la probabilidad esta mal calibrada, el ROI estimado puede ser engañoso.

Referencia: `Credit Risk Modeling using Excel and VBA-Wiley - Wiley (2007).pdf`.

## Metricas recomendadas

| Metrica | Uso en Datathon | Lectura bancaria |
|---|---|---|
| AUC-ROC | Ranking global | Capacidad de separar buenos/malos |
| Gini | Scoring clasico | `2*AUC - 1` |
| KS | Separacion | Distancia maxima entre distribuciones |
| PR-AUC | Desbalance | Calidad sobre clase default |
| Brier | Calibracion | Probabilidad confiable |
| Log Loss | Penalizacion probabilistica | Castiga exceso de confianza |
| Lift@10% | Concentracion | Cuantos malos captura la cola de riesgo |
| ROI | Negocio | Beneficio de la politica |
| Gap train/valid | Overfitting | Estabilidad del modelo |

Fuentes internas: `Credit Risk Modeling using Excel and VBA-Wiley - Wiley (2007).pdf`, `RCO 4 - Modelos de pérdida esperada 2026.pdf`.

## Politica de negocio recomendada

Usar tres bandas:

| Banda | Regla | Decision | Mensaje de negocio |
|---|---|---|---|
| Bajo riesgo | `prob_default <= u_bajo` | Aprobar | Cliente rentable y sano |
| Riesgo medio | `u_bajo < prob_default <= u_alto` | Condicionar | Menor linea, aval o revision |
| Alto riesgo | `prob_default > u_alto` | Rechazar/prevenir | Default esperado supera margen |

Matriz economica sugerida si el caso usa costos como los documentos master:

| Real / Decision | Aprobar | Rechazar |
|---|---:|---:|
| Buen pagador | +450 | -150 |
| Default | -3000 | 0 |

Referencia: `RCO 4 - Modelos de pérdida esperada 2026.pdf`.  
Recomendacion aplicada al caso: optimizar umbrales por ahorro neto vs aprobar todos, no solo por F1.

## Interpretabilidad

Entregables recomendados:

- Feature importance global.
- SHAP beeswarm si el modelo lo permite.
- Tabla de top variables con interpretacion bancaria.
- Perfil de cada banda de riesgo.
- Ejemplos de falsos positivos y falsos negativos.

Traduccion de variables:

- Alto `ratio_endeudamiento`: menor capacidad de absorcion.
- Bajo `score_buro`: peor historial externo.
- `buro_sin_historial`: incertidumbre por no bancarizacion.
- Alta `dias_mora_prev`: comportamiento pasado de atraso.
- Canal/region: posible heterogeneidad de originacion o contexto.

Fuentes internas: `S5 Modelo de Credit Scoring - Salvador Rayo.pdf`, `Credit Risk Modeling using Excel and VBA-Wiley - Wiley (2007).pdf`.

## Ciclos economicos y macro

Si hay variables de fecha o periodo:

- Validar por tiempo.
- Medir default por cohorte.
- Revisar si el modelo se degrada en periodos recientes.
- Crear features de periodo o vintage.

Si hay variables regionales:

- Cruzar region con default.
- Proponer monitoreo de desempleo/inflacion/tasas por zona si no estan en la data.

Fuente interna: `RCO 1 Crisis financiera.pdf`, `Scopus 2019 Gestión del riesgo crediticio. un análisis de datos de panel sobre los bancos islámicos en Turquía.pdf`.

Recomendacion aplicada al caso: aunque no haya macro en datos, incluir como limitacion y recomendacion de produccion.

## Errores comunes que debemos evitar

- Entregar solo AUC sin explicar negocio.
- Usar `accuracy` como metrica central.
- No revisar leakage.
- Imputar nulos sin flags.
- No calibrar `prob_default`.
- Usar redes neuronales opacas como champion sin explicacion.
- Hacer Optuna largo y quedarse sin submission.
- Presentar threshold 0.50 sin optimizacion economica.
- No guardar `feature_builder.py` para test.

## Ideas potentes para diferenciarnos

1. Mostrar grafico de default real por banda de score.
2. Mostrar curva de calibracion.
3. Presentar matriz economica de errores.
4. Mostrar politica de 3 bandas con ahorro estimado.
5. Incluir una lectura de ciclo economico y monitoreo.
6. Explicar nulos como "sin historial" o "informalidad", no como basura.
7. Presentar dos modelos: champion predictivo y Logit explicable.
8. Conectar variables top con acciones bancarias.

## Storytelling recomendado para PPT

Estructura de 10 slides:

1. Problema: incremento de mora y necesidad de originacion responsable.
2. Datos: target, poblacion, variables, tasa default.
3. Riesgo bancario: PD, perdida esperada y costos.
4. EDA: señales principales de riesgo.
5. Feature engineering: capacidad de pago, historial, endeudamiento.
6. Modelos: comparativa y champion.
7. Validacion: AUC, Gini, KS, Brier, Lift.
8. Interpretabilidad: variables que explican default.
9. Politica de 3 bandas y ROI.
10. Recomendaciones y monitoreo post-implementacion.

## Checklist operativo

Antes de enviar:

- [ ] `submission.csv` tiene `id_cliente` y `prob_default`.
- [ ] No hay columnas ID dentro del modelo.
- [ ] No hay leakage confirmado.
- [ ] El notebook corre de inicio a fin.
- [ ] Hay baseline y champion.
- [ ] Hay AUC/Gini/KS/Brier.
- [ ] Hay politica de 3 bandas.
- [ ] Hay interpretabilidad.
- [ ] Los supuestos financieros estan marcados.

## Referencias internas indicando de que archivo salio cada idea

- Scoring y decision: `RCO 2 - Análisis del Scoring de Crédito 2026.pdf`, `S5 Modelo de Credit Scoring - Salvador Rayo.pdf`.
- Logit y PD: `RCO 5 - Modelos de incumplimiento Logit 2026.pdf`, `Credit Risk Modeling using Excel and VBA-Wiley - Wiley (2007).pdf`.
- Perdida esperada: `RCO 4 - Modelos de pérdida esperada 2026.pdf`.
- Basilea/SBS: `S4 El Nuevo Acuerdo de Basilea para Riesgo de Crédito.pdf`, `9. Reg. de Requerimiento de Patrimonio Efectivo por Riesgo de Crédito_Res. SBS N° 14354-2009.pdf`.
- Variables de mora: `RCO 3 Análisis variables que afecta la mora 2026.pdf`.
- Microfinanzas: `Paper Loan repayment behavior among the clients of Indian microfinance.pdf`.
- Cooperativas y calidad de cartera: `SISTEMA DE MONITOREO PERLAS.pdf`.
- Arboles: `S6 Gestión de Riesgo y arboles decision.pdf`.
- Redes neuronales: `S7 Redes Neuronales y Evaluación de Créditos Financieros.pdf`.
- Crisis/ciclo: `RCO 1 Crisis financiera.pdf`.

## Distribución estratégica del trabajo del equipo

### Perfil 1: Financista

Responsabilidades concretas:

- Interpretar el caso desde rentabilidad, mora, provision y perdida esperada.
- Definir matriz de costos: buen aprobado, buen rechazado, default aprobado, default rechazado.
- Revisar variables financieras: ingreso, deuda, ratio de endeudamiento, mora previa, score buro.
- Preparar la politica de 3 bandas.
- Incorporar ciclo economico: bonanza, crisis, recesion, inflacion, tasas y desempleo.

Archivos o secciones debe revisar:

- `RCO 4 - Modelos de pérdida esperada 2026.pdf`
- `S4 El Nuevo Acuerdo de Basilea para Riesgo de Crédito.pdf`
- `RCO 3 Análisis variables que afecta la mora 2026.pdf`
- `SISTEMA DE MONITOREO PERLAS.pdf`

Entregables:

- Matriz economica de errores.
- Texto de impacto financiero.
- Recomendacion por banda de riesgo.
- Validacion de interpretacion de variables top.

Conexion con el modelo final:

- Convierte `prob_default` en decision bancaria y ROI.

Preguntas que debe responder:

- Que threshold maximiza beneficio neto?
- Que costo tiene aprobar un cliente moroso?
- Que variables representan capacidad de pago?
- Que recomendacion bancaria sale de cada banda?

### Perfil 2: Ingeniera ambiental

Responsabilidades concretas:

- Revisar variables externas, territoriales, sociales o ESG.
- Analizar region, canal, sector o entorno si aparecen en datos.
- Conectar contexto macro/local con probabilidad de incumplimiento.
- Apoyar interpretacion de variables no tradicionales.

Archivos o secciones debe revisar:

- `RCO 1 Crisis financiera.pdf`
- `Scopus 2025 FinTech, gestión de riesgos y banca de crédito verde.pdf`
- `Scopus 2016 Factores que influyen en la adopción del crédito agrícola como estrategia de gestión de riesgos.pdf`
- `Emerald Banca móvil un concepto de moda o un canal institucionalizado en la banca minorista del futuro (1).pdf`

Entregables:

- Analisis de default por region/canal.
- Hipotesis de riesgo territorial.
- Recomendaciones de variables externas futuras.
- Slide de contexto y diferenciador.

Conexion con el modelo final:

- Enriquece la explicacion del riesgo y ayuda a contar una historia mas completa que "el modelo predijo".

Preguntas que debe responder:

- Que segmentos territoriales o canales tienen mayor default?
- Hay señales de inclusion financiera o vulnerabilidad?
- Que variables externas deberia monitorear el banco?
- El riesgo podria cambiar con crisis, inflacion o desempleo?

### Perfil 3: Perfil tecnico / data science / ingenieria de sistemas

Responsabilidades concretas:

- Ejecutar EDA, limpieza y anti-leakage.
- Construir features reproducibles.
- Entrenar y comparar modelos.
- Calibrar probabilidades.
- Optimizar threshold y politica.
- Generar notebook final y submission.

Archivos o secciones debe revisar:

- `Credit Risk Modeling using Excel and VBA-Wiley - Wiley (2007).pdf`
- `RCO 5 - Modelos de incumplimiento Logit 2026.pdf`
- `S6 Gestión de Riesgo y arboles decision.pdf`
- `S7 Redes Neuronales y Evaluación de Créditos Financieros.pdf`

Entregables:

- Notebook reproducible.
- `feature_builder.py`.
- `submission.csv`.
- Tabla de modelos.
- Graficos ROC/PR/calibracion.
- SHAP o feature importance.

Conexion con el modelo final:

- Implementa el motor predictivo y produce los artefactos evaluables.

Preguntas que debe responder:

- El pipeline evita leakage?
- Que modelo gana y por que?
- La probabilidad esta calibrada?
- Cuales son los falsos negativos mas caros?
- La submission se genera con el mismo feature engineering que train?

## Cierre

La estrategia ganadora es una combinacion de rigor tecnico y criterio bancario: un modelo robusto, validado, interpretable y conectado a una politica de aprobacion rentable. Las fuentes revisadas respaldan tres ideas centrales: predecir PD, traducirla a perdida/ROI y gobernar el modelo con validacion, calibracion y monitoreo.
