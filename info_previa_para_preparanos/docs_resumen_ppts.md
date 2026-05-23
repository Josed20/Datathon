# Resumen Aplicado de PPTs y Diapositivas de Riesgo Crediticio

## Objetivo del documento

Convertir las presentaciones y materiales tipo diapositiva de `docs/` en conocimiento aplicable para una Datathon bancaria de riesgo crediticio. El foco es seleccionar ideas accionables para EDA, feature engineering, modelamiento, validacion, interpretabilidad y storytelling de negocio.

## Fuentes revisadas

No se encontraron archivos `.pptx`; todos los materiales de la carpeta son PDFs. Se clasificaron como PPTs o diapositivas los documentos con estructura de clase, sesion o exposicion:

- `RCO 1 - La Gestión del Riesgo de crédito 2026.pdf`
- `RCO 1 Crisis financiera.pdf`
- `RCO 2 - Análisis del Scoring de Crédito 2026.pdf`
- `RCO 3 - Análisis del Riesgo de Crédito.pdf`
- `RCO 3 Análisis variables que afecta la mora 2026.pdf`
- `RCO 4 - Modelos de pérdida esperada 2026.pdf`
- `RCO 5 - Modelos de incumplimiento Logit 2026.pdf`
- `RCO 10 - Cobertura de riesgo de crédito con derivados 2026.pdf`
- `RCO 12 - Riesgo operativo.pdf`
- `RCO 13 - Riesgo operativo.pdf`
- `RCO 14 - Continuidad y seguridad de la informacion.pdf`
- `S4 El Nuevo Acuerdo de Basilea para Riesgo de Crédito.pdf`
- `S5 Modelo de Credit Scoring - Salvador Rayo.pdf`
- `S6 Gestión de Riesgo y arboles decision.pdf`
- `S7 Redes Neuronales y Evaluación de Créditos Financieros.pdf`
- `S7 Redes neuronales y el Riesgo de Crédito.pdf`
- `S7 Redes-Neunorales de Riesgo 2021.pdf`
- `IRB REQ CAPITAL RIESGO OPERACIONAL.pdf`
- `SISTEMA DE MONITOREO PERLAS.pdf`
- `RIESGO DE LAVADO DE ACTIVOS.pdf`

Duplicados exactos detectados:

- `RCO 10 - Cobertura de riesgo de crédito con derivados 2026.pdf` y su copia `(1)`.
- `S7 Redes neuronales y el Riesgo de Crédito.pdf` y su copia `(1)`.

## Conceptos clave

### Riesgo crediticio como perdida esperada

La idea central para el caso es que el modelo no debe predecir por predecir, sino estimar riesgo economico. La perdida esperada se estructura como:

```text
EL = PD x EAD x LGD
```

- `PD`: probabilidad de incumplimiento.
- `EAD`: exposicion al momento del default.
- `LGD`: perdida dado el incumplimiento.

Fuente interna: `RCO 4 - Modelos de pérdida esperada 2026.pdf`, `S4 El Nuevo Acuerdo de Basilea para Riesgo de Crédito.pdf`.

Aplicacion al caso: aunque la Datathon pida `prob_default`, la narrativa ganadora debe conectar esa probabilidad con perdida evitada, aprobacion responsable, provision y rentabilidad.

### Scoring como sistema de decision

El scoring no es solo un algoritmo. Es una forma de ordenar solicitantes por riesgo y transformar ese orden en reglas de negocio: aprobar, condicionar o rechazar.

Fuente interna: `RCO 2 - Análisis del Scoring de Crédito 2026.pdf`, `S5 Modelo de Credit Scoring - Salvador Rayo.pdf`.

Aplicacion al caso:

- Bajo riesgo: aprobacion automatica.
- Riesgo medio: menor linea, garantia, aval o revision manual.
- Alto riesgo: rechazo preventivo.

### Logit como modelo base defendible

El modelo Logit estima una probabilidad acotada entre 0 y 1 y se presta bien para explicar efectos de variables. Es un baseline fuerte para banca porque permite interpretar direccion, magnitud y odds.

Fuente interna: `RCO 5 - Modelos de incumplimiento Logit 2026.pdf`, `S5 Modelo de Credit Scoring - Salvador Rayo.pdf`.

Recomendacion aplicada al caso: entrenar Logit siempre, aunque el champion sea boosting. Sirve como modelo explicable, benchmark y respaldo ante jurado.

### Variables que afectan mora

Las diapositivas enfatizan que clientes o empresas altamente apalancadas, poco liquidas o poco rentables suelen ser menos confiables. Tambien aparece la importancia del historial de pago y comportamiento previo.

Fuente interna: `RCO 3 Análisis variables que afecta la mora 2026.pdf`, `RCO 3 - Análisis del Riesgo de Crédito.pdf`.

Aplicacion al caso:

- `ratio_endeudamiento`: variable critica.
- `dias_mora_prev`: debe interpretarse como historial de atraso.
- `score_buro`: debe tratar nulos como posible "sin historial".
- `ingreso_mensual`: base para capacidad de pago.

### Basilea, capital y garantias

Basilea y SBS conectan la calificacion de riesgo con requerimientos de capital, exposicion, garantias y validacion interna. No es necesario implementar capital regulatorio completo, pero si usar el lenguaje correcto.

Fuente interna: `S4 El Nuevo Acuerdo de Basilea para Riesgo de Crédito.pdf`, `9. Reg. de Requerimiento de Patrimonio Efectivo por Riesgo de Crédito_Res. SBS N° 14354-2009.pdf`.

Aplicacion al caso:

- Hablar de PD, LGD, EAD y provision fortalece la presentacion.
- Si hay garantias, deben reducir perdida esperada, no necesariamente probabilidad de default.
- Si no hay garantias en datos, marcar como limitacion.

### PERLAS y calidad de cartera

PERLAS plantea monitoreo financiero de cooperativas con foco en proteccion, estructura financiera, calidad de activos, rendimientos, liquidez y senales de crecimiento. Para Datathon, lo mas util es la vision de calidad de cartera y provision contra morosidad.

Fuente interna: `SISTEMA DE MONITOREO PERLAS.pdf`.

Aplicacion al caso:

- Construir narrativa de cartera: tasa de default por segmento, provision esperada y concentracion de riesgo.
- Evitar quedarse solo en precision del modelo.

### Crisis, ciclos economicos y contexto macro

Las diapositivas sobre crisis financiera recuerdan que el riesgo de credito cambia por ciclo: bonanza, recesion, desempleo, inflacion, tasas y liquidez. En una Datathon, esto se vuelve diferenciador si el dataset tiene fecha, region, canal o sector.

Fuente interna: `RCO 1 Crisis financiera.pdf`, `RCO 1 - La Gestión del Riesgo de crédito 2026.pdf`.

Recomendacion aplicada al caso: si existe columna temporal, hacer validacion temporal y mostrar estabilidad por periodo. Si no existe, mencionar la limitacion y proponer monitoreo de drift macro.

## Metodos utiles

### EDA crediticio

- Revisar distribucion del target y tasa de default.
- Revisar missingness como senal, no solo como problema tecnico.
- Comparar variables por buenos vs. malos pagadores.
- Analizar monotonicidad esperada: mayor deuda/ingreso deberia elevar riesgo; mayor score buro deberia reducirlo.
- Segmentar por region, canal, empleo y bandas de ingreso.
- Detectar outliers economicos reales: ingresos altos, deudas altas, lineas extremas.

Fuentes internas: `RCO 2 - Análisis del Scoring de Crédito 2026.pdf`, `RCO 3 Análisis variables que afecta la mora 2026.pdf`, `SISTEMA DE MONITOREO PERLAS.pdf`.

### Feature engineering recomendado

| Variable base | Feature sugerida | Justificacion | Fuente |
|---|---|---|---|
| `ingreso_mensual` | `ingreso_missing`, `log_ingreso`, ingreso capado | Capacidad de pago y robustez ante valores extremos | `RCO 3 Análisis variables que afecta la mora 2026.pdf` |
| `saldo_deudor_total` + ingreso | `ratio_deuda_ingreso` | Apalancamiento individual | `RCO 3 Análisis variables que afecta la mora 2026.pdf` |
| `ratio_endeudamiento` | cap, log, flags alto/medio | Relacion deuda-capacidad; proteger outliers | Recomendacion aplicada al caso |
| `score_buro` | `buro_sin_historial`, score corregido | Nulo puede significar cliente no bancarizado | `S5 Modelo de Credit Scoring - Salvador Rayo.pdf` |
| `dias_mora_prev` | `sin_mora_previa`, mora capada, mora log | Historial de pago es predictor fuerte | `RCO 3 Análisis variables que afecta la mora 2026.pdf` |
| region/canal | default rate solo dentro de CV o one-hot | Heterogeneidad territorial/canal | Recomendacion aplicada al caso |
| fecha/periodo | vintage, cohorte, ciclo | Capturar cambios por ciclo economico | `RCO 1 Crisis financiera.pdf` |

### Modelamiento

Modelos prioritarios:

- Dummy baseline: prueba de sanidad.
- Logistic Regression: interpretabilidad y benchmark.
- Random Forest o HistGradientBoosting: no linealidad rapida.
- LightGBM/XGBoost/CatBoost: candidatos champion si estan instalados.
- Redes neuronales: challenger solo si hay tiempo y suficiente data; no usarlas como narrativa principal si sacrifican interpretabilidad.

Fuentes internas: `RCO 5 - Modelos de incumplimiento Logit 2026.pdf`, `S6 Gestión de Riesgo y arboles decision.pdf`, `S7 Redes Neuronales y Evaluación de Créditos Financieros.pdf`.

## Variables importantes

Variables directas para riesgo de impago:

- Ingreso mensual.
- Ratio de endeudamiento.
- Saldo deudor total.
- Score buro.
- Dias de mora previa.
- Numero o severidad de atrasos.
- Tipo de empleo.
- Antiguedad laboral si existe.
- Edad si existe, con control de rangos imposibles.
- Zona geografica.
- Canal de captacion.
- Garantias si existen.

Variables de contexto:

- Periodo de originacion.
- Region.
- Sector economico.
- Canal digital vs. presencial.
- Variables macro si el caso las trae: inflacion, desempleo, tasas, crisis/recesion.

## Aplicacion directa al caso de riesgo crediticio

El caso debe presentarse como una solucion de originacion crediticia:

1. El modelo estima `prob_default`.
2. La probabilidad se valida con AUC, Gini, KS y calibracion.
3. El banco transforma el score en politica:
   - Bajo riesgo: aprobar.
   - Riesgo medio: aprobar condicionado.
   - Alto riesgo: rechazar o pedir garantia.
4. La decision se mide por impacto financiero, no solo por accuracy.

Fuente interna: `RCO 4 - Modelos de pérdida esperada 2026.pdf`, `S5 Modelo de Credit Scoring - Salvador Rayo.pdf`.

## Recomendaciones para EDA

- Empezar con target rate y balance de clases.
- Construir tabla de missingness con interpretacion de negocio.
- Graficar `score_buro`, `ratio_endeudamiento`, ingreso y mora previa contra default.
- Crear bandas de score, ingreso y endeudamiento.
- Evaluar si los nulos tienen mayor o menor default.
- Identificar segmentos: region, canal, tipo de empleo.
- Revisar duplicados por `id_cliente`.
- Revisar si hay variables post-evento o leakage.

## Recomendaciones para modelamiento

- Split estratificado por defecto; temporal solo si hay fecha real.
- No imputar ni codificar antes del split.
- Usar class weights antes que SMOTE como primera opcion.
- Comparar Logit vs. modelos de arboles.
- Seleccionar champion por AUC/KS/Gini y estabilidad.
- Calibrar probabilidad si se usara para decision economica.
- Guardar importancia de variables o SHAP.

## Metricas recomendadas

- AUC-ROC: discriminacion global.
- Gini: `2*AUC - 1`, lenguaje comun en scoring.
- KS: separacion entre buenos y malos pagadores.
- Brier Score: calidad de probabilidad.
- Log Loss: penaliza probabilidades mal calibradas.
- Lift@10%: concentracion de malos en la cola de mayor riesgo.
- ROI por threshold: impacto de aprobar/rechazar.
- Overfitting gap: diferencia train/valid.

Fuentes internas: `Credit Risk Modeling using Excel and VBA-Wiley - Wiley (2007).pdf`, `RCO 4 - Modelos de pérdida esperada 2026.pdf`, `RCO 5 - Modelos de incumplimiento Logit 2026.pdf`.

## Errores comunes que debemos evitar

- Usar accuracy como metrica principal en datos desbalanceados.
- Tratar nulos de buro como simple mediana sin flag.
- Aplicar target encoding antes del split.
- Usar variables futuras o posteriores al default.
- No calibrar `prob_default` antes de convertirla en politica de aprobacion.
- Presentar redes neuronales como caja negra sin explicabilidad.
- Optimizar F1 y olvidar el costo asimetrico: default aprobado cuesta mucho mas que buen cliente rechazado.

## Ideas potentes para diferenciarnos en la Datathon

- Mostrar matriz economica: buen aprobado, buen rechazado, default aprobado, default rechazado.
- Presentar politica de 3 bandas y no solo un threshold.
- Incluir grafico de calibracion de probabilidad.
- Mostrar top segmentos con mayor default real.
- Traducir SHAP/importancias a lenguaje bancario.
- Explicar limitaciones regulatorias y de ciclo economico.
- Incluir una diapositiva de monitoreo post-modelo: drift, tasa de default por cohorte, recalibracion.

## Distribución estratégica del trabajo del equipo

### Perfil 1: Financista

Responsabilidades concretas:

- Traducir PD, LGD, EAD y perdida esperada a negocio.
- Definir matriz economica de aprobacion/rechazo.
- Interpretar ratio de endeudamiento, capacidad de pago, mora previa y score.
- Construir narrativa de provisiones, rentabilidad y politica de credito.
- Incorporar lectura de ciclo economico: bonanza, crisis, recesion, inflacion, tasas y desempleo.

Archivos o secciones a revisar:

- `RCO 4 - Modelos de pérdida esperada 2026.pdf`
- `S4 El Nuevo Acuerdo de Basilea para Riesgo de Crédito.pdf`
- `RCO 3 Análisis variables que afecta la mora 2026.pdf`
- `SISTEMA DE MONITOREO PERLAS.pdf`

Entregables:

- Tabla de costos/beneficios.
- Interpretacion de las variables top.
- Recomendaciones de politica de 3 bandas.
- Slide de impacto financiero.

Conexion con el modelo final:

- Valida que el threshold no sea solo estadistico, sino rentable.
- Da sentido bancario a las probabilidades.

Preguntas que debe responder:

- Que cuesta mas: aprobar un mal pagador o rechazar un buen pagador?
- Que variables explican capacidad de pago?
- Que politica aplicaria el banco por banda?

### Perfil 2: Ingeniera ambiental

Responsabilidades concretas:

- Analizar variables externas, region, territorio y canal.
- Buscar patrones de riesgo por zona geografica o contexto social.
- Apoyar interpretacion de variables no tradicionales.
- Identificar posibles señales ESG si aparecen en los datos.
- Conectar riesgo crediticio con vulnerabilidad territorial o sectorial.

Archivos o secciones a revisar:

- `RCO 1 Crisis financiera.pdf`
- `Scopus 2025 FinTech, gestión de riesgos y banca de crédito verde.pdf`
- `Redes Neuronales y Regresión a Bonos Verdes.pdf`
- `RCO 3 Análisis variables que afecta la mora 2026.pdf`

Entregables:

- Analisis por region/canal.
- Hipotesis de riesgo territorial.
- Recomendaciones para segmentacion no tradicional.
- Texto para slide de contexto.

Conexion con el modelo final:

- Ayuda a explicar heterogeneidad regional/canal y a evitar una lectura puramente tecnica.

Preguntas que debe responder:

- Hay zonas con default sistematicamente mayor?
- El canal digital o presencial cambia el riesgo?
- Hay señales de vulnerabilidad social, ambiental o sectorial?

### Perfil 3: Data science / ingenieria de sistemas

Responsabilidades concretas:

- Ejecutar EDA, limpieza, features, split y modelos.
- Controlar leakage y reproducibilidad.
- Entrenar baseline, Logit, arboles y boosting.
- Calcular AUC, Gini, KS, Brier, Lift y ROI.
- Generar submission, graficos e interpretabilidad.

Archivos o secciones a revisar:

- `RCO 5 - Modelos de incumplimiento Logit 2026.pdf`
- `S6 Gestión de Riesgo y arboles decision.pdf`
- `S7 Redes Neuronales y Evaluación de Créditos Financieros.pdf`
- `Credit Risk Modeling using Excel and VBA-Wiley - Wiley (2007).pdf`

Entregables:

- Notebook final reproducible.
- `submission.csv`.
- Tabla comparativa de modelos.
- Curvas ROC/PR/calibracion.
- Feature importance/SHAP.

Conexion con el modelo final:

- Convierte conocimiento bancario en variables, modelos y decisiones medibles.

Preguntas que debe responder:

- El modelo discrimina bien?
- Esta calibrada la probabilidad?
- Hay overfitting?
- Que variables explican el default?
