# Resumen Aplicado de Libros, Papers y Documentos Largos de Riesgo Crediticio

## Objetivo del documento

Extraer teoria util y aplicable desde libros, papers, normativa y documentos tecnicos de `docs/` para robustecer una solucion de Datathon bancaria de riesgo crediticio. Este documento no resume todo el contenido; selecciona lo que puede mejorar EDA, feature engineering, modelamiento, validacion, interpretabilidad y presentacion.

## Fuentes revisadas

### Libros y capitulos tecnicos

- `Credit Risk Modeling using Excel and VBA-Wiley - Wiley (2007).pdf`
- `Libro Quantitative_Finance Credit_Risk_Modeling- Wile_.pdf`
- `1 APOSTOLINK - Fund del riesgo bancario - Cap 4 Riesgo de crédito.pdf`
- `3 BREALEY MYERS - Gestión de créditos - Capitulo 32.pdf`
- `S5 Pilar Gomez  Antonio Portal - Gestión y control de riesgo de crédito en la banca  Capítulo 2.pdf`
- `metodologia_de_la_investigacion_-_roberto_hernandez_sampieri.pdf`

### Normativa y documentos regulatorios

- `5. Reg. de Gobierno Corporativo_Res. SBS N° 272-2017.pdf`
- `SBS  Resolución 272-2017 Reglamento de Gobierno Corporativo y GIR.pdf`
- `9. Reg. de Requerimiento de Patrimonio Efectivo por Riesgo de Crédito_Res. SBS N° 14354-2009.pdf`
- `SBS atrimonio Efectivo por Riesgo de Crédito,  1088-2024.r.pdf`
- `S4 El Nuevo Acuerdo de Basilea para Riesgo de Crédito.pdf`

### Papers y estudios aplicados

- `Paper Loan repayment behavior among the clients of Indian microfinance.pdf`
- `EBSCO-Loan repayment behavior among the clients of Indian microfinance institutions.pdf`
- `Paper Factores de riesgo crediticio de los prestatarios,.pdf`
- `Emerald Qué impulsa crédito riesgo de microfinanzas instituciones (1).pdf`
- `Paper Modelo-de-diagnóstico-para-medir-el-desempeño-financiero-en-las-cooperativas.pdf`
- `Paper Modelo-de-diagnóstico-para-medir-el-desempeño-financiero-en-las-cooperativas (1).pdf`
- `modelo logit para bankruptcy.pdf`
- `modelo logit para bankruptcy (1).pdf`
- `Paper Redes Neuronales en la Finanzas.pdf`
- `Redes Neuronales en la Evaluación de RC.pdf`
- `Riesgo de Crédito y Redes Neuronales.pdf`
- `Riesgo de Crédito y Redes Neuronales (1).pdf`
- `Scopus 2016 Riesgo y gestión de riesgos en la industria de tarjetas de crédito.pdf`
- `Scopus 2019 Gestión del riesgo crediticio. un análisis de datos de panel sobre los bancos islámicos en Turquía.pdf`
- `Scopus 2025 FinTech, gestión de riesgos y banca de crédito verde.pdf`
- `Scopus 2016 Factores que influyen en la adopción del crédito agrícola como estrategia de gestión de riesgos.pdf`
- `Emerald Banca móvil un concepto de moda o un canal institucionalizado en la banca minorista del futuro (1).pdf`
- `Emerald Alineando la inclusión financiera y la integridad financiera.pdf`
- `Emerald EEl gobierno corporativo en las cajas de ahorros españolas y su relación con la rentabilidad.pdf`

### Duplicados exactos detectados

- `Paper Loan repayment behavior among the clients of Indian microfinance.pdf` duplica a `EBSCO-Loan repayment behavior among the clients of Indian microfinance institutions.pdf`.
- `Emerald Alineando la inclusión financiera y la integridad financiera.pdf` duplica a su copia `(1)`.
- `Riesgo de Crédito y Redes Neuronales.pdf` duplica a su copia `(1)`.

## Conceptos clave

### Score, probabilidad de default y comportamiento observado

`Credit Risk Modeling using Excel and VBA-Wiley - Wiley (2007).pdf` plantea el scoring como un puente entre variables explicativas, score, probabilidad de default y comportamiento observado. La idea mas aplicable es que el score debe poder traducirse a una probabilidad interpretable y validada.

Aplicacion directa:

- El output `prob_default` debe ser una probabilidad, no solo un ranking.
- Si se usa para decision de credito, debe revisarse calibracion.
- Un score con buen AUC pero mala calibracion puede ordenar bien, pero asignar probabilidades economicamente peligrosas.

### Logit como herramienta natural de scoring

Los documentos de Logit y scoring muestran que la regresion logistica es adecuada porque restringe la probabilidad al rango `[0, 1]` y permite explicar los efectos de las variables.

Fuentes internas:

- `RCO 5 - Modelos de incumplimiento Logit 2026.pdf`
- `S5 Modelo de Credit Scoring - Salvador Rayo.pdf`
- `Credit Risk Modeling using Excel and VBA-Wiley - Wiley (2007).pdf`
- `modelo logit para bankruptcy.pdf`

Aplicacion directa:

- Usar Logistic Regression con `class_weight='balanced'` como baseline.
- Comparar sus signos con intuicion bancaria.
- Si una variable se comporta contraintuitivamente, revisar leakage, outlier o segmentacion.

### Validacion de ratings y scores

`Credit Risk Modeling using Excel and VBA-Wiley - Wiley (2007).pdf` incluye validacion con CAP/ROC, Brier Score y pruebas de calibracion de probabilidades. Esto es especialmente util para defender el modelo ante jurado.

Aplicacion directa:

- Reportar AUC y Gini para discriminacion.
- Reportar KS para separacion de buenos y malos.
- Reportar Brier Score y curva de calibracion para confiabilidad de probabilidades.
- Mostrar Lift@10% si se quiere explicar concentracion de malos pagadores en la cola de riesgo.

### Riesgo crediticio bajo Basilea y SBS

Basilea y normativa SBS enfatizan estructura de capital, exposicion, probabilidad de incumplimiento, perdida dado incumplimiento, garantias, ponderacion de riesgo y validacion.

Fuentes internas:

- `S4 El Nuevo Acuerdo de Basilea para Riesgo de Crédito.pdf`
- `9. Reg. de Requerimiento de Patrimonio Efectivo por Riesgo de Crédito_Res. SBS N° 14354-2009.pdf`
- `5. Reg. de Gobierno Corporativo_Res. SBS N° 272-2017.pdf`

Aplicacion directa:

- Usar lenguaje regulatorio: PD, LGD, EAD, provision, capital, apetito de riesgo.
- No confundir garantia con menor probabilidad de default; la garantia reduce perdida esperada o severidad.
- Explicar que el modelo apoya originacion, seguimiento y provision.

### Microfinanzas y clientes no bancarizados

Los papers de microfinanzas resaltan variables de hogar, ingreso, endeudamiento, moral hazard, region y caracteristicas del prestamo como determinantes de mora o repago.

Fuentes internas:

- `Paper Loan repayment behavior among the clients of Indian microfinance.pdf`
- `Emerald Qué impulsa crédito riesgo de microfinanzas instituciones (1).pdf`
- `S5 Modelo de Credit Scoring - Salvador Rayo.pdf`

Aplicacion directa:

- Los nulos de historial crediticio pueden ser informacion, no error.
- El sobreendeudamiento es una señal clave.
- Region/canal pueden reflejar acceso, vulnerabilidad o calidad de originacion.
- En clientes no bancarizados, variables alternativas pueden ganar peso.

### Diagnostico financiero y cooperativas

Los documentos sobre cooperativas y PERLAS destacan calidad de cartera, provisiones, solvencia, liquidez y monitoreo de morosidad.

Fuentes internas:

- `SISTEMA DE MONITOREO PERLAS.pdf`
- `Paper Modelo-de-diagnóstico-para-medir-el-desempeño-financiero-en-las-cooperativas.pdf`
- `1_FORANEO_01_20_Análisis+financiero+de+la+cartera+de+crédito+de+la+Cooperativa de Ahorro y Crédito CACPE.pdf`

Aplicacion directa:

- En presentacion, hablar de calidad de cartera y default evitado.
- Simular provision o perdida evitada por banda.
- Si el reto involucra microcreditos, conectar con sostenibilidad de cartera.

### Redes neuronales y modelos no lineales

Los documentos de redes neuronales muestran su utilidad para capturar relaciones no lineales, pero su limitacion principal en banca es explicabilidad.

Fuentes internas:

- `Paper Redes Neuronales en la Finanzas.pdf`
- `Redes Neuronales en la Evaluación de RC.pdf`
- `Riesgo de Crédito y Redes Neuronales.pdf`
- `S7 Redes Neuronales y Evaluación de Créditos Financieros.pdf`

Aplicacion directa:

- Usar redes solo como challenger si hay tiempo.
- Priorizar boosting interpretable con SHAP antes que una red opaca.
- Si una red mejora marginalmente pero no explica, no conviene como champion de Datathon bancaria.

### Ciclos economicos, crisis y macro

Los documentos de crisis y estudios de riesgo bancario recuerdan que el riesgo de credito no es estacionario. Cambia con empleo, inflacion, tasas, liquidez, shocks sectoriales y ciclo economico.

Fuentes internas:

- `RCO 1 Crisis financiera.pdf`
- `Scopus 2019 Gestión del riesgo crediticio. un análisis de datos de panel sobre los bancos islámicos en Turquía.pdf`
- `Scopus 2016 Riesgo y gestión de riesgos en la industria de tarjetas de crédito.pdf`
- `Scopus 2025 FinTech, gestión de riesgos y banca de crédito verde.pdf`

Aplicacion directa:

- Si hay fecha, crear variables de cohorte o periodo.
- Si hay region/sector, analizar heterogeneidad territorial o sectorial.
- Incluir monitoreo de drift como recomendacion de gobierno del modelo.

## Metodos utiles

### Metodos estadisticos

- Regresion logistica para PD.
- Probit como alternativa conceptual, no prioritaria en Datathon.
- Arboles y boosting para no linealidad.
- Redes neuronales como benchmark secundario.
- Validacion ROC/CAP/Gini/KS.
- Calibracion con Brier Score y reliability plot.

### Metodos de segmentacion

- Bandas por probabilidad de default.
- Segmentos por endeudamiento.
- Segmentos por ingreso/capacidad de pago.
- Segmentos por score buro.
- Segmentos por canal de captacion.
- Segmentos territoriales.
- Segmentos por historial de mora.

### Metodos de negocio

- Politica de 3 bandas.
- Matriz de costo-beneficio.
- Perdida esperada aproximada.
- Champion/challenger.
- Monitoreo de drift y recalibracion.

## Variables importantes

| Familia | Variables utiles | Razon bancaria | Fuente |
|---|---|---|---|
| Capacidad de pago | ingreso, empleo, antiguedad, edad | Mide sostenibilidad del pago | `RCO 3 Análisis variables que afecta la mora 2026.pdf` |
| Endeudamiento | deuda/ingreso, ratio endeudamiento, saldo deudor | Sobreapalancamiento eleva default | `Paper Loan repayment behavior...pdf` |
| Historial | score buro, mora previa, atrasos | Comportamiento pasado predice repago | `S5 Modelo de Credit Scoring - Salvador Rayo.pdf` |
| Producto | monto, plazo, tasa, cuota, garantia | Define exposicion e incentivos | `S4 El Nuevo Acuerdo de Basilea...pdf` |
| Canal | app, web, asesor, presencial | Captura calidad de originacion o autoseleccion | `Emerald Banca móvil...pdf` |
| Territorio | zona, region, sector | Riesgo contextual y acceso financiero | `Scopus 2016 Factores...crédito agrícola...pdf` |
| Macro | inflacion, desempleo, tasas, crisis | Riesgo cambia por ciclo economico | `RCO 1 Crisis financiera.pdf` |

## Aplicacion directa al caso de riesgo crediticio

Para la Datathon, el conocimiento debe convertirse en estos artefactos:

- EDA con lectura bancaria.
- Features de capacidad de pago y endeudamiento.
- Modelo champion con probabilidades calibradas.
- Politica de tres bandas.
- ROI por decision.
- Explicabilidad global y local.
- Recomendaciones de originacion y monitoreo.

## Recomendaciones para EDA

1. Verificar target `default_90d` y su tasa.
2. Revisar nulos por variable y default rate de nulos.
3. Graficar distribuciones por target.
4. Crear bandas de riesgo exploratorias.
5. Revisar variables con sentido economico:
   - mayor endeudamiento -> mas riesgo;
   - mayor score buro -> menor riesgo;
   - mayor mora previa -> mas riesgo.
6. Revisar outliers financieros, no eliminarlos automaticamente.
7. Detectar leakage:
   - saldos o mora posterior al evento;
   - variables de cobranza post-default;
   - aprobacion manual futura;
   - estado final del credito.

## Recomendaciones para modelamiento

1. Baseline Dummy.
2. Logistic Regression interpretable.
3. Random Forest o HistGradientBoosting.
4. LightGBM/XGBoost/CatBoost si disponibles.
5. `class_weight` o `scale_pos_weight` como primera respuesta al desbalance.
6. Calibracion sigmoid si mejora Brier.
7. Threshold por ROI, no por 0.50.
8. Politica final en tres bandas.

## Metricas recomendadas

| Metrica | Para que sirve | Fuente |
|---|---|---|
| AUC-ROC | Discriminacion global | `Credit Risk Modeling using Excel and VBA-Wiley - Wiley (2007).pdf` |
| Gini | Lenguaje clasico de scoring | `Credit Risk Modeling using Excel and VBA-Wiley - Wiley (2007).pdf` |
| KS | Separacion maxima entre buenos y malos | `Credit Risk Modeling using Excel and VBA-Wiley - Wiley (2007).pdf` |
| Brier Score | Calidad de probabilidad | `Credit Risk Modeling using Excel and VBA-Wiley - Wiley (2007).pdf` |
| Log Loss | Penaliza mala confianza probabilistica | Recomendacion aplicada al caso |
| Lift@10% | Concentracion en cola de riesgo | Recomendacion aplicada al caso |
| ROI | Decision financiera | `RCO 4 - Modelos de pérdida esperada 2026.pdf` |

## Errores comunes que debemos evitar

- Usar modelos complejos sin baseline.
- Medir solo accuracy.
- No separar entrenamiento y validacion antes del preprocesamiento.
- Ignorar calibracion.
- Usar SMOTE sin justificar; puede distorsionar probabilidad.
- Tratar nulos como ruido cuando pueden representar ausencia de historial.
- No traducir metricas a politica bancaria.
- Ignorar ciclo economico si el dataset tiene periodo.

## Ideas potentes para diferenciarnos en la Datathon

- Presentar el modelo como motor de originacion responsable.
- Mostrar un mapa o tabla de riesgo por zona/canal.
- Usar `EL = PD x EAD x LGD` como marco conceptual, aunque se aproxime con costos del caso.
- Mostrar curva de calibracion.
- Presentar matriz economica de errores.
- Integrar interpretabilidad con recomendaciones: "subir revision manual para perfiles con alta deuda/ingreso y bajo score buro".
- Proponer monitoreo post-implementacion: drift, tasa de default real por banda, recalibracion.

## Referencias internas por idea

- Logit y PD: `RCO 5 - Modelos de incumplimiento Logit 2026.pdf`, `Credit Risk Modeling using Excel and VBA-Wiley - Wiley (2007).pdf`.
- Validacion ROC/CAP/Brier: `Credit Risk Modeling using Excel and VBA-Wiley - Wiley (2007).pdf`.
- Perdida esperada: `RCO 4 - Modelos de pérdida esperada 2026.pdf`.
- Basilea/SBS: `S4 El Nuevo Acuerdo de Basilea para Riesgo de Crédito.pdf`, `9. Reg. de Requerimiento de Patrimonio Efectivo por Riesgo de Crédito_Res. SBS N° 14354-2009.pdf`.
- Microfinanzas y repago: `Paper Loan repayment behavior among the clients of Indian microfinance.pdf`.
- Cooperativas y calidad de cartera: `SISTEMA DE MONITOREO PERLAS.pdf`, `Paper Modelo-de-diagnóstico-para-medir-el-desempeño-financiero-en-las-cooperativas.pdf`.
- Redes neuronales: `S7 Redes Neuronales y Evaluación de Créditos Financieros.pdf`, `Riesgo de Crédito y Redes Neuronales.pdf`.
- Ciclos/crisis: `RCO 1 Crisis financiera.pdf`.

## Distribución estratégica del trabajo del equipo

### Perfil 1: Financista

Responsabilidades concretas:

- Leer las fuentes de perdida esperada, Basilea, SBS y PERLAS.
- Definir costos de decisiones y supuestos financieros.
- Interpretar variables de endeudamiento, ingreso, mora y capacidad de pago.
- Preparar narrativa de provision, capital y rentabilidad.

Archivos o secciones debe revisar:

- `RCO 4 - Modelos de pérdida esperada 2026.pdf`
- `S4 El Nuevo Acuerdo de Basilea para Riesgo de Crédito.pdf`
- `9. Reg. de Requerimiento de Patrimonio Efectivo por Riesgo de Crédito_Res. SBS N° 14354-2009.pdf`
- `SISTEMA DE MONITOREO PERLAS.pdf`

Entregables:

- Matriz de costo-beneficio.
- Politica de aprobacion por banda.
- Interpretacion de variables financieras.
- Slide de impacto economico.

Conexion con el modelo final:

- Convierte `prob_default` en decision de negocio.

Preguntas clave:

- Cual es la perdida esperada por aprobar malos clientes?
- Cual es el costo de rechazar buenos clientes?
- Que variable justifica mejor la decision ante un comite?

### Perfil 2: Ingeniera ambiental

Responsabilidades concretas:

- Revisar contexto territorial, canal, inclusion financiera y green/ESG si aparece.
- Analizar si region o sector explican riesgo.
- Preparar hipotesis de vulnerabilidad territorial o economica.

Archivos o secciones debe revisar:

- `Scopus 2025 FinTech, gestión de riesgos y banca de crédito verde.pdf`
- `Scopus 2016 Factores que influyen en la adopción del crédito agrícola como estrategia de gestión de riesgos.pdf`
- `Emerald Banca móvil un concepto de moda o un canal institucionalizado en la banca minorista del futuro (1).pdf`
- `RCO 1 Crisis financiera.pdf`

Entregables:

- Segmentacion territorial/canal.
- Lectura de contexto externo.
- Ideas de variables no tradicionales.
- Texto de storytelling para PPT.

Conexion con el modelo final:

- Aporta explicacion de riesgo no capturada solo por ratios financieros.

Preguntas clave:

- Que regiones/canales concentran mayor riesgo?
- Hay variables ambientales, sociales o territoriales en el dataset?
- Como cambia el riesgo bajo crisis o shocks?

### Perfil 3: Data science / ingenieria de sistemas

Responsabilidades concretas:

- Ejecutar pipeline tecnico.
- Construir features.
- Entrenar modelos.
- Validar probabilidades.
- Generar submission.
- Exportar graficos e interpretabilidad.

Archivos o secciones debe revisar:

- `Credit Risk Modeling using Excel and VBA-Wiley - Wiley (2007).pdf`
- `RCO 5 - Modelos de incumplimiento Logit 2026.pdf`
- `S6 Gestión de Riesgo y arboles decision.pdf`
- `S7 Redes Neuronales y Evaluación de Créditos Financieros.pdf`

Entregables:

- Notebook ejecutable.
- Tabla de modelos.
- Curvas ROC/PR/calibracion.
- SHAP o feature importance.
- `submission.csv`.

Conexion con el modelo final:

- Materializa la teoria en un modelo medible y reproducible.

Preguntas clave:

- El modelo discrimina y calibra?
- El pipeline evita leakage?
- El resultado se puede reproducir rapido?
