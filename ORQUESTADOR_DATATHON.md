# 🎯 ORQUESTADOR MAESTRO — Sistema de Documentos para Datathon

> **Documento 3 de 3 — FLUJO PRINCIPAL** | Coordina: `EDA_Guia_Datathon_Banca.md` (Doc 1) y `Modelado_Validacion_Datathon_Banca.md` (Doc 2)
>
> **Este es el punto de entrada.** Cuando recibes un nuevo caso de datathon, lee ESTE documento primero.

---

## ARQUITECTURA DEL SISTEMA

```
┌─────────────────────────────────────────────────────┐
│  🎯 ORQUESTADOR (Este documento)                   │
│                                                     │
│  FASE 0: Leer caso → Extraer TODA la información   │
│  FASE 1: Invocar Doc 1 (EDA)                       │
│  FASE 2: Invocar Doc 2 (Modelado)                  │
│  FASE 3: Verificar excelencia                       │
│  FASE 4: Análisis de negocio                        │
│  FASE 5: Generar entregables                        │
│                                                     │
│    ↓ pasa contexto             ↓ pasa features      │
│  ┌──────────────┐   ────→   ┌──────────────────┐   │
│  │ 📊 EDA (D1)  │           │ 🤖 MODELO (D2)   │   │
│  │ Calidad      │           │ Entrenamiento     │   │
│  │ Exploración  │           │ Validación        │   │
│  │ Features     │           │ Evaluación        │   │
│  │ Selección    │           │ Interpretabilidad │   │
│  └──────────────┘   ←────   └──────────────────┘   │
│    ↑ loop si métricas insuficientes                 │
└─────────────────────────────────────────────────────┘
```

---

## CONTRATO UNICO ENTRE DOCUMENTOS

### Alcance operativo

Este sistema esta optimizado para una datathon bancaria supervisada de **scoring de credito**. Su ruta ejecutable por defecto es `clasificacion_binaria` para estimar `default_90d` y construir una politica de 3 bandas de riesgo. La Fase 0 puede detectar regresion, multiclase, ranking, clustering o anomalias, pero si el caso no es clasificacion binaria de default se debe adaptar el Doc 2 antes de entrenar: metricas, modelos, umbrales, gates y entregables no se ejecutan literalmente.

### Responsabilidades que no se mezclan

| Documento | Es dueno de | No debe hacer |
|---|---|---|
| Orquestador | Leer el caso, fijar supuestos, elegir estrategia de validacion, coordinar gates y entregables | Inventar columnas, metricas o restricciones que no salgan del caso/datos |
| EDA (Doc 1) | Calidad, leakage review, decisiones por variable, features reproducibles fila a fila y handoff al modelado | Ajustar imputadores, encoders, escaladores, winsorizacion o seleccion final usando todo el dataset |
| Modelado (Doc 2) | Split train/val/test, `fit` del preprocesamiento solo en train, comparacion de modelos, threshold, interpretabilidad y serializacion | Cambiar el target o ignorar decisiones de leakage sin devolver feedback al EDA |

### Contratos de handoff

1. La salida de Fase 0 se guarda como `reports/case_config.json` y es la fuente de verdad para el EDA.
2. El EDA entrega `data/processed/features.parquet` con target, IDs necesarios y features reproducibles. Puede conservar nulos; el Doc 2 los trata dentro de pipelines ajustados solo con train.
3. El EDA entrega `reports/eda_handoff.json` con claves canonicas de nivel superior: `target_col`, `id_cols`, `metrica_jurado`, `tipo_problema`, `validation_strategy`, `periodo_col`, `group_col`, `feature_builder_path` y `status`.
4. Si existe test sin target o submission, la misma ingenieria de features usada en train debe vivir en `src/feature_builder.py` o en una funcion equivalente reutilizable. No se predice sobre test raw con un preprocessor entrenado sobre features que test aun no tiene.
5. Si un gate queda en `BLOCKED`, el siguiente documento no interpreta el bloqueo como aprobado: devuelve feedback especifico al documento anterior.

---

## FASE 0 — EXTRACCIÓN DEL CASO (Minuto 0 a 25)

### Regla cardinal

```
ANTES DE ESCRIBIR UNA SOLA LÍNEA DE CÓDIGO,
EXTRAER TODA LA INFORMACIÓN DEL CASO.
CADA DATO NO EXTRAÍDO ES UNA OPORTUNIDAD PERDIDA.
```

---

### 0.2 Información del evento

| Campo | Valor | Fuente |
|---|---|---|
| Nombre del datathon | Datathon ESAN 2026 | Presentación / Slides |
| Institución organizadora | Universidad ESAN | Presentación / Slides |
| Universidad/Empresa anfitriona | Biblioteca ESAN | Presentación / Slides |
| Empresa/Banco del caso | FinanCrece S.A. (Entidad peruana) | Presentación / Slides |
| Fecha del evento | 23 de Mayo de 2026 | Presentación / Slides |
| Duración total disponible | 3 horas efectivas de desarrollo | Aclaración operativa del equipo |
| Formato de entrega | `.ipynb` limpio + `submission.csv` + `Diapositivas PPT` (máx 10) | Presentación / Slides |
| Email o plataforma de envío | datafest@esan.edu.pe | Presentación / Slides |
| Hora límite de entrega | 15:30 (Cierre estricto) | Presentación / Slides |

---

### 0.3 Problema de negocio

| Campo | Valor |
|---|---|
| ¿Qué quiere resolver el negocio? | Detener el incremento sostenido de la mora mediante un modelo predictivo robusto. |
| ¿Cuál es el dolor o impacto actual? | Incremento de la mora del 4.2% al 7.8% (+3.6 pp) en 18 meses, erosionando la rentabilidad. |
| ¿Cuántos clientes/transacciones/casos afecta? | Segmento completo de consumo, créditos PYME y microcréditos (especialmente clientes no bancarizados). |
| ¿Qué decisión tomará el banco con el modelo? | Segmentar la cartera en 3 bandas de riesgo y definir límites de crédito diferenciados o rechazos preventivos. |
| ¿Quién es el usuario final del modelo? | Analistas de riesgo de crédito, gerencia de riesgos minoristas y sistema automático de evaluación. |
| ¿Qué métrica de negocio importa? | ROI Financiero Neto (Intereses de buenos clientes vs. pérdida de capital de morosos). |
| ¿Existe un costo conocido del problema? | VN (Pagador aprobado) = +$450; FP (Pagador rechazado) = -$150; FN (Default aprobado) = -$3,000; VP = $0. |
| ¿Hay regulación aplicable? | SBS (Superintendencia de Banca y Seguros de Perú), provisiones por riesgo de crédito. |

---

### 0.4 Problema técnico

| Campo | Valor |
|---|---|
| Tipo de problema | Clasificación binaria altamente desbalanceada (Default / No Default) |
| Variable objetivo (nombre exacto de la columna) | `default_90d` |
| Codificación del target | 0 = Al día / Pagador puntual; 1 = Default (mora mayor a 90 días) |
| Métrica oficial del jurado (si se especifica) | AUC-ROC, Estadística KS, Coeficiente Gini ($2 \times \text{AUC} - 1$) y Precisión |
| Métrica secundaria recomendada | KS, Gini, Brier Score, Lift@10 y ROI; F1 solo como diagnóstico operativo |
| ¿Hay dataset de test separado sin target? | Sí (archivo de prueba provisto por el organizador, 10K filas aprox.) |
| ¿Hay que generar archivo submission? | Sí |
| Formato del submission | Archivo CSV con columnas `id_cliente` y `prob_default` |

---

### 0.5 Datos disponibles

| Archivo | Formato | Tamaño | Filas estimadas | Columnas | Descripción |
|---|---|---|---|---|---|
| Archivo de entrenamiento provisto | .csv/.xlsx | Por confirmar | 40,000 aprox. | 18 aprox. | Dataset histórico con target real `default_90d` |
| Archivo de prueba provisto | .csv/.xlsx | Por confirmar | 10,000 aprox. | 17 aprox. | Dataset de prueba sin target para `submission.csv` |

**Detectar automáticamente:**

```python
from pathlib import Path

ROOT = Path('.')
data_files = []
for ext in ['*.xlsx', '*.csv', '*.sav', '*.parquet', '*.json', '*.xls']:
    data_files.extend(ROOT.rglob(ext))

for f in data_files:
    size_mb = f.stat().st_size / 1024 / 1024
    print(f"  {f.name} | {size_mb:.1f} MB | {f.suffix}")
```

---

### 0.6 Variables clave identificadas del caso

| Variable | Tipo | Rol | Descripción del caso | Notas |
|---|---|---|---|---|
| `default_90d` | numérica | target | Mora acumulada > 90 días | Binario (0/1) |
| `edad` | numérica | feature | Edad del solicitante | Numérica. Validar valores negativos (ruido) |
| `ingreso_mensual` | numérica | feature | Ingreso neto declarado | Numérica. Tratar nulos intencionales y outliers extremos |
| `score_buro` | numérica | feature | Historial crediticio externo | Numérica. Nulos significan clientes **sin historial formal** |
| `dias_mora_prev` | numérica | feature | Días máximos de mora previa | Numérica. Nulos significan clientes **sin deudas/atrasos previos** |
| `ratio_endeudamiento` | numérica | feature | Deuda total / Ingresos | Relación continua de apalancamiento financiero |
| `tipo_empleo` | categórica | feature | Relación laboral del solicitante | Dependiente / Independiente |
| `zona_geografica` | categórica | feature | Región de procedencia del cliente | Lima, Norte, Sur, Centro, Oriente |
| `canal_captacion` | categórica | feature | Canal de venta | Presencial, App, Web, Asesor |
| `id_cliente` | numérica | id | Identificador del cliente | Excluir del entrenamiento |

---

### 0.7 Contexto de negocio extraído

Responder todas estas preguntas buscando en el caso:

```markdown
- Industria: Microfinanzas y Crédito de Consumo Bancario
- País: Perú (SBS regulaciones aplicables)
- Período de los datos: Solicitudes históricas 2022 - 2024, sujeto a confirmación contra columnas reales.
- ¿Es snapshot único o serie temporal?: Tratar como snapshot si no existe columna de fecha/periodo; usar validación temporal solo si el dataset trae una columna cronológica confiable.
- Tamaño del universo de clientes: 50,000 registros
- Tasa del evento (si se menciona): 22% de tasa de default aproximada en train
- ¿Datos anonimizados?: Sí, IDs codificados
- ¿Hay información de productos financieros?: Líneas de crédito y saldo deudor general
- ¿Hay información transaccional/de canales?: Sí, canal de captación de solicitudes
- ¿Hay información crediticia?: Historial de mora previo, consultas central y buró
- ¿Hay información demográfica?: Edad y zona geográfica de procedencia
- ¿Hay variables de rentabilidad?: Ingresos y ratios de endeudamiento
- Matriz de valor crediticio (si se menciona): Pérdida promedio por default = $3,000 USD vs. ganancia neta por buen pagador = $450 USD. Costo de rechazo erróneo = $150 USD.
- ¿Se mencionan políticas actuales de originación/cobranza?: No se mencionan políticas activas, requiere política de aprobación desde cero.
- Restricciones de privacidad o regulación: SBS regulación de provisiones, exclusión de IDs personales en modelos.
```

---

### 0.8 Criterios de evaluación del jurado

| Componente | Peso | Qué evalúa | Cómo ganar puntos |
|---|---|---|---|
| Calidad del modelo predictivo | 30% | Desempeño métricas: AUC-ROC, KS, Gini, Precisión y estabilidad inter-temporal | AUC alto, sobreajuste controlado (< 0.05) y CV limpia |
| Interpretabilidad | 25% | Explicación del impacto de las variables a nivel global e individual | SHAP beeswarm plot, explicabilidad en términos de negocio |
| Impacto de Negocio | 25% | Cuantificación del beneficio financiero, simulación de mora y políticas | Política de 3 bandas de riesgo justificada con ROI |
| Presentación oral final | 20% | Estructura narrativa, storytelling del caso, claridad en Q&A | Diapositivas limpias, foco en negocio e impacto financiero |

---

### 0.9 Preguntas no resueltas

Lista de información que el caso NO provee pero sería valiosa:

1. ¿Cuál es la tasa de aprobación histórica bajo el scoring tradicional manual?
2. ¿Existen variables de comportamiento adicionales del cliente dentro de FinanCrece (ej: saldo promedio en cuentas de ahorros)?
3. ¿Cuál es el costo operacional de una evaluación manual en la banda de riesgo medio?

**Acción:** documentar como supuestos razonables usando `[SUPUESTO]` bajo la guía del Financista del equipo.

---

## FASE 1 — INVOCAR DOCUMENTO DE EDA (Doc 1)

### 1.1 Qué pasar al EDA

Después de llenar la Fase 0, construir el diccionario de contexto para el EDA:

```python
orquestador_a_eda = {
    'target_col': 'default_90d',         # target crediticio
    'tipo_problema': 'clasificacion_binaria',
    'metrica_jurado': 'roc_auc',         # principal métrica discriminatoria
    'data_paths': ['dataInicial/[archivo_train_provisto]'],
    'id_cols': ['id_cliente'],           # excluir identificadores
    'date_cols': [],                      # fechas conocidas
    'periodo_col': None,
    'group_col': None,
    'validation_strategy': 'stratified_split', # cambiar a temporal_split solo si existe fecha/periodo confiable
    'known_leakage_vars': [],
    'contexto_negocio': 'Scoring de Riesgo de Crédito para FinanCrece S.A. enfocándose en reducir mora del 7.8% al 4.2%.',
    'drop_cols': [],
    'restricciones': ['solo usar variables provistas'],
    'test_raw_path': 'dataInicial/[archivo_test_provisto]',
    'submission_spec': {'cols': ['id_cliente', 'prob_default'], 'format': 'csv'},
    'priority_analysis': ['score_buro', 'ingreso_mensual', 'ratio_endeudamiento'],
    'random_state': 42,
    'time_budget_minutes': 30,           # budget real: 3 horas totales
}
```

Guardar este diccionario en `reports/case_config.json`. El EDA puede cargarlo y mapear estas claves a sus constantes (`TARGET_COL`, `ID_COLS`, etc.).

### 1.2 Qué esperar del EDA (outputs)

| Artefacto | Ruta | Descripción |
|---|---|---|
| Dataset original guardado | `data/processed/base_original.parquet` | Base de referencia sin feature engineering |
| Dataset con features | `data/processed/features.parquet` | Features reproducibles, IDs requeridos y target; nulos permitidos para el pipeline |
| Lista de features | `data/processed/feature_list.txt` | Orden de predictors entregados al Doc 2 |
| Resumen del EDA | `reports/eda_summary.csv` | Tabla de variables con estadísticos |
| Diccionario de features | `reports/feature_dictionary.csv` | Descripción de cada variable |
| Decisiones por variable | `reports/variable_decisions.csv` | Mantener, eliminar, transformar o revisar |
| Reporte de calidad | `reports/data_quality_report.json` | Nulos, duplicados, target y dimensiones |
| Handoff | `reports/eda_handoff.json` | Contrato canonico para iniciar Doc 2 |
| Feature builder | `src/feature_builder.py` | Misma ingenieria para train y test cuando haya submission |
| Figuras del EDA | `reports/figures/*.png` | Gráficos de exploración |

### 1.3 Gate de calidad del EDA

Antes de pasar al modelado, verificar:

- [ ] ¿Se identificó correctamente el target y su distribución?
- [ ] ¿Se analizaron nulos y se documento su tratamiento dentro del pipeline?
- [ ] ¿Se ejecuto al menos una ronda de feature engineering util y reproducible? Si los datos lo permiten, apuntar a 15-20 features con sentido de negocio.
- [ ] ¿Se documentó la decisión de cada variable (mantener/eliminar/transformar)?
- [ ] ¿Se verificó que no hay leakage?
- [ ] ¿Los datos están listos para que Doc 2 haga el split sin `fit` previo sobre todo el dataset?
- [ ] ¿La ingenieria que necesite test/submission quedo reutilizable?
- [ ] ¿Se guardaron los artefactos en las rutas esperadas?

**Si algún gate falla:** volver al EDA con instrucciones específicas de qué corregir.

---

## FASE 2 — INVOCAR DOCUMENTO DE MODELADO (Doc 2)

### 2.1 Qué pasar al Modelado

```python
orquestador_a_modelo = {
    'features_path': 'data/processed/features.parquet',
    'target_col': '___',
    'id_cols': ['___'],
    'metrica_jurado': 'roc_auc',
    'metric_secondary': 'f1',
    'validation_strategy': '___',     # stratified_split / temporal_split / group_split
    'periodo_col': None,
    'group_col': None,
    'feature_builder_path': 'src/feature_builder.py',
    'test_size': 0.20,
    'random_state': 42,
    'excellence_threshold_auc': 0.85,
    'max_overfitting_gap': 0.05,
    'time_budget_minutes': 120,
    'eda_findings': {
        'tasa_evento': 0.0,           # ej: 0.1546
        'n_features_originales': 0,
        'n_features_creadas': 0,
        'variables_con_muchos_nulos': [],
        'top_variables_correlacion': [],
    },
}
```

Estas claves deben coincidir con `reports/eda_handoff.json`. El JSON del EDA es la entrada autoritativa del Doc 2; este bloque solo permite verificar u overridear lo decidido por el Orquestador.

### 2.2 Árbol de decisión para validación

```
¿Hay variable de fecha con múltiples períodos?
├── SÍ → ¿El problema es predecir el futuro?
│   ├── SÍ → VALIDACIÓN TEMPORAL
│   │       Entrenar con períodos antiguos, validar con recientes.
│   └── NO → Split estratificado
│           Pero documentar que existe temporalidad.
└── NO → ¿Cada fila es un cliente/entidad única?
    ├── SÍ → SPLIT ESTRATIFICADO 60/20/20
    │       train/val/test con stratify=y, random_state=42
    └── NO → ¿Hay múltiples filas por cliente?
        ├── SÍ → GROUP SPLIT por customer_id
        │       Mismo cliente NO puede estar en train y test.
        └── NO → SPLIT ESTRATIFICADO (default seguro)
```

### 2.3 Qué esperar del Modelado (outputs)

| Artefacto | Ruta | Descripción |
|---|---|---|
| Modelo entrenado | `models/best_model.joblib` | Modelo ganador serializado |
| Preprocessor | `models/preprocessor.joblib` | Pipeline de preprocesamiento |
| Metadata | `models/model_metadata.json` | Parámetros, features, métricas |
| Log de experimentos | `reports/experiment_log.csv` | Comparativa de todos los modelos |
| Análisis de threshold | `reports/threshold_analysis.csv` | Precision/Recall/F1/ROI por threshold |
| Feature importance | `reports/feature_importance.csv` | Importancia de variables |
| Predicciones | `reports/predicciones_validacion.csv` | Scores del mejor modelo en validación |
| Figuras de evaluación | `reports/figures/*.png` | ROC, PR, confusión, lift, SHAP |

### 2.4 Gate de calidad del Modelo

Verificar antes de continuar:

- [ ] ¿Se entrenaron mínimo 4 modelos (Dummy, LogReg, RF y un boosting; 5+ si hay librerías instaladas)?
- [ ] ¿Hay tabla comparativa con métricas consistentes?
- [ ] ¿El overfitting gap del mejor modelo es < 0.05?
- [ ] ¿Se optimizó el threshold?
- [ ] ¿Se calculó SHAP o feature importance?
- [ ] ¿Se guardaron todos los artefactos?

---

## FASE 3 — VERIFICACIÓN DE EXCELENCIA

### 3.1 Umbrales de excelencia para Default / Riesgo Crediticio

| Métrica | Mediocre | Aceptable | Bueno | Excelente | Sospechoso |
|---|---|---|---|---|---|
| ROC-AUC | < 0.65 | 0.65 - 0.75 | 0.75 - 0.83 | 0.83 - 0.92 | > 0.95 |
| Gini | < 0.30 | 0.30 - 0.50 | 0.50 - 0.66 | 0.66 - 0.84 | > 0.90 |
| KS | < 0.25 | 0.25 - 0.40 | 0.40 - 0.50 | 0.50 - 0.60 | > 0.65 |
| Brier Score | > 0.25 | 0.18 - 0.25 | 0.12 - 0.18 | < 0.12 | 0.00 sospechoso |
| Gap train/valid AUC | > 0.08 | 0.05 - 0.08 | 0.03 - 0.05 | < 0.03 | AUC valid > train |
| ROI policy | Negativo | Leve positivo | Positivo y defendible | Alto y estable | Depende de fuga/leakage |

**Lectura bancaria:** AUC/Gini/KS miden discriminacion; Brier y calibracion miden si la probabilidad sirve para tomar decisiones economicas. Para el reto, un modelo con AUC moderado pero ROI, KS y explicabilidad fuertes puede superar a un modelo opaco con AUC marginalmente mayor.

---

### 3.2 Árbol de diagnóstico y acción

```
¿ROC-AUC >= 0.75 y KS >= 0.30?
├── SÍ → ¿Gap train/valid AUC <= 0.05?
│   ├── SÍ → Continuar a calibracion, ROI y politica de 3 bandas.
│   └── NO → Regularizar: menor depth, mayor min_child/min_samples, early stopping.
│           Reentrenar una sola vez y comparar con baseline.
└── NO → ¿ROC-AUC >= 0.65?
    ├── SÍ → Competitivo debil: mejorar features de riesgo crediticio.
    │       Prioridad:
    │       1. Nulos como señal: buro sin historial, mora previa ausente, ingreso ausente.
    │       2. Ratios seguros: deuda/ingreso, monto/ingreso, apalancamiento capado.
    │       3. Revisar outliers y monotonicidad esperada.
    │       4. Probar class_weight o scale_pos_weight antes que SMOTE.
    └── NO → Bloqueo serio.
            Verificar target, mapping 0/1, IDs, leakage, columnas constantes
            y si el train corresponde realmente al caso de FinanCrece.
```

---

### 3.3 Protocolo de mejora iterativa

Si las métricas no son excelentes, iterar con este protocolo:

| Iteración | Acción | Tiempo máximo | Criterio de salida |
|---|---|---|---|
| 1 | Feature engineering adicional crediticio (Doc 1) | 20 min | +0.015 AUC o +0.04 KS |
| 2 | Ajuste ligero de hiperparametros (Doc 2) | 15 min | +0.01 AUC sin subir gap |
| 3 | Calibracion sigmoid/isotonic (Doc 2) | 10 min | Mejor Brier sin perder >0.01 AUC |
| 4 | Revisión de leakage y variables (Doc 1) | 10 min | Confirmar limpieza |

**Regla de corte:** Con solo 3 horas, si una iteracion no mejora, congelar el mejor modelo y mover energia a ROI, explicabilidad y PPT. El jurado valora mas una solucion bancaria defendible que un AUC marginalmente mayor.

---

## FASE 4 — ANÁLISIS DE NEGOCIO

### 4.1 Framework de impacto financiero

#### Parámetros base de decision crediticia

```python
# === MATRIZ ECONOMICA DEL CASO ===
# Convencion: target default_90d = 1 indica mora > 90 dias.

GANANCIA_BUEN_APROBADO = 450      # VN: pagador aprobado
COSTO_BUEN_RECHAZADO = -150       # FP: oportunidad perdida / friccion comercial
PERDIDA_DEFAULT_APROBADO = -3000  # FN: capital perdido por moroso aprobado
VALOR_DEFAULT_RECHAZADO = 0       # VP: perdida evitada

# Banda media: aprobacion condicionada con menor exposicion.
FACTOR_EXPOSICION_MEDIA = 0.50    # [SUPUESTO] limite/linea reducida al 50%
```

#### Cálculo de ROI por threshold de rechazo

```python
import numpy as np
import pandas as pd

def calcular_roi_crediticio_por_threshold(
    y_true,
    y_proba,
    thresholds,
    ganancia_buen_aprobado=450,
    costo_buen_rechazado=-150,
    perdida_default_aprobado=-3000,
    valor_default_rechazado=0,
):
    """Evalua la politica binaria: aprobar si p(default) < threshold; rechazar si p(default) >= threshold."""
    resultados = []

    for t in thresholds:
        rechazar = (y_proba >= t).astype(int)
        aprobar = 1 - rechazar

        buenos = (y_true == 0)
        malos = (y_true == 1)

        buenos_aprobados = int(((aprobar == 1) & buenos).sum())
        buenos_rechazados = int(((rechazar == 1) & buenos).sum())
        defaults_aprobados = int(((aprobar == 1) & malos).sum())
        defaults_rechazados = int(((rechazar == 1) & malos).sum())

        beneficio_modelo = (
            buenos_aprobados * ganancia_buen_aprobado
            + buenos_rechazados * costo_buen_rechazado
            + defaults_aprobados * perdida_default_aprobado
            + defaults_rechazados * valor_default_rechazado
        )

        beneficio_aprobar_todos = (
            int(buenos.sum()) * ganancia_buen_aprobado
            + int(malos.sum()) * perdida_default_aprobado
        )

        ahorro_neto = beneficio_modelo - beneficio_aprobar_todos
        roi = ahorro_neto / max(abs(beneficio_aprobar_todos), 1)

        resultados.append({
            'threshold_rechazo': round(float(t), 3),
            'buenos_aprobados': buenos_aprobados,
            'buenos_rechazados': buenos_rechazados,
            'defaults_aprobados': defaults_aprobados,
            'defaults_rechazados': defaults_rechazados,
            'beneficio_modelo_usd': round(float(beneficio_modelo), 2),
            'beneficio_base_aprobar_todos_usd': round(float(beneficio_aprobar_todos), 2),
            'ahorro_neto_usd': round(float(ahorro_neto), 2),
            'roi_vs_base': round(float(roi), 4),
        })

    return pd.DataFrame(resultados)
```

#### Politica de 3 bandas de riesgo

```python
def simular_politica_3_bandas(
    y_true,
    y_proba,
    u_bajo,
    u_alto,
    factor_exposicion_media=0.50,
):
    """
    Bajo riesgo: aprobar linea completa.
    Riesgo medio: aprobar condicionado con menor exposicion.
    Alto riesgo: rechazar o enviar a evaluacion excepcional.
    """
    buenos = (y_true == 0)
    malos = (y_true == 1)

    bajo = y_proba <= u_bajo
    medio = (y_proba > u_bajo) & (y_proba <= u_alto)
    alto = y_proba > u_alto

    beneficio = (
        ((bajo & buenos).sum() * GANANCIA_BUEN_APROBADO)
        + ((bajo & malos).sum() * PERDIDA_DEFAULT_APROBADO)
        + ((medio & buenos).sum() * GANANCIA_BUEN_APROBADO * factor_exposicion_media)
        + ((medio & malos).sum() * PERDIDA_DEFAULT_APROBADO * factor_exposicion_media)
        + ((alto & buenos).sum() * COSTO_BUEN_RECHAZADO)
        + ((alto & malos).sum() * VALOR_DEFAULT_RECHAZADO)
    )

    return {
        'u_bajo': round(float(u_bajo), 3),
        'u_alto': round(float(u_alto), 3),
        'clientes_bajo': int(bajo.sum()),
        'clientes_medio': int(medio.sum()),
        'clientes_alto': int(alto.sum()),
        'beneficio_politica_usd': round(float(beneficio), 2),
        'tasa_default_bajo': round(float(y_true[bajo].mean()), 4) if bajo.sum() else np.nan,
        'tasa_default_medio': round(float(y_true[medio].mean()), 4) if medio.sum() else np.nan,
        'tasa_default_alto': round(float(y_true[alto].mean()), 4) if alto.sum() else np.nan,
    }
```

#### Matriz de costo-beneficio

```
┌────────────────────────────────────────────────────────────┐
│                  DECISION DEL MODELO                       │
│                                                            │
│                 Aprobar             Rechazar               │
│  Real    ┌──────────────────┬──────────────────────┐       │
│  Bueno   │ VN: buen pagador │ FP: buen cliente     │       │
│  (0)     │ aprobado         │ rechazado            │       │
│          │ +450 USD         │ -150 USD             │       │
│  ────────┼──────────────────┼──────────────────────┤       │
│  Default │ FN: moroso       │ VP: default evitado  │       │
│  (1)     │ aprobado         │ por rechazo          │       │
│          │ -3000 USD        │ 0 USD                │       │
│          └──────────────────┴──────────────────────┘       │
└────────────────────────────────────────────────────────────┘
```

---

### 4.2 Perfil del cliente en riesgo

Generar una tabla que muestre las características promedio por cuartil de score:

```python
def crear_perfil_riesgo(X_val, y_val, y_proba, feature_cols):
    """Crea perfil comparativo por cuartil de riesgo."""
    perfil = X_val[feature_cols].copy()
    perfil['score'] = y_proba
    perfil['target'] = y_val.values
    perfil['cuartil'] = pd.qcut(
        perfil['score'], q=4,
        labels=['Bajo', 'Medio', 'Alto', 'Muy Alto']
    )

    resumen = perfil.groupby('cuartil').agg({
        'score': 'mean',
        'target': 'mean',
    })

    # Agregar estadísticos de features top
    for col in feature_cols[:10]:  # top 10 features
        if perfil[col].dtype in ['float64', 'int64']:
            resumen[col] = perfil.groupby('cuartil')[col].mean()

    return resumen
```

---

### 4.3 Recomendaciones de negocio (plantilla)

```markdown
## Recomendaciones para el Banco

### Acciones inmediatas (0-30 días)
1. **Implementar politica de 3 bandas de riesgo** sobre solicitudes nuevas.
   - Bajo riesgo: aprobar linea completa si `prob_default <= [u_bajo]`.
   - Riesgo medio: aprobacion condicionada, menor linea o revision manual si `[u_bajo] < prob_default <= [u_alto]`.
   - Alto riesgo: rechazar preventivamente o exigir garantias si `prob_default > [u_alto]`.
2. **Monitorear señales de alerta** identificadas por el modelo:
   - [Variable 1]: clientes con [comportamiento] tienen [X]x más riesgo.
   - [Variable 2]: [descripción del patrón].

### Acciones a mediano plazo (1-6 meses)
3. **Ajustar limites por rentabilidad y riesgo:**
   - Clientes rentables + bajo riesgo: acelerar aprobacion.
   - Clientes rentables + riesgo medio: aprobar con menor exposicion y monitoreo temprano.
   - Clientes de alto riesgo: rechazar, pedir garantia o derivar a producto alternativo.
4. **Integrar el score con originacion** para alertas automaticas a analistas de credito.

### Acciones estratégicas (6-12 meses)
5. **Reentrenar el modelo mensualmente** con datos frescos.
6. **Implementar champion/challenger** para medir mora real por cohorte.
7. **Construir dashboard de monitoreo** con drift detection.
```

---

## FASE 5 — GENERACIÓN DE ENTREGABLES

### 5.1 Notebook de entrega (.ipynb)

Estructura exacta de celdas:

```
CELDA 1 (Markdown): Portada
    # 🏦 Datathon — [Título del Problema]
    ## [Universidad] | [Equipo] | [Fecha]
    ### Resumen: [Modelo] con ROC-AUC=[X], F1=[Y], Lift@10%=[Z]x

CELDA 2 (Code): Imports y configuración
    - Todos los imports necesarios
    - Configuración de rutas con pathlib
    - Constantes: TARGET_COL, RANDOM_SEED, etc.
    - Dark mode matplotlib
    - Suprimir warnings

CELDA 3 (Code): Carga de datos
    - Lectura del archivo original
    - print shape, dtypes, head(3)
    - Markdown: "Dataset de X clientes con Y variables"

CELDA 4 (Markdown + Code): Planteamiento del problema
    - Texto: qué es el problema y por qué importa
    - Gráfico: distribución del target
    - Conclusión: "Tasa de evento: X% — desbalance moderado/fuerte"

CELDA 5 (Markdown + Code): EDA — Hallazgos principales
    - SOLO los 4-5 gráficos más impactantes
    - Cada gráfico con conclusión en markdown

CELDA 6 (Markdown + Code): Feature Engineering
    - Texto: explicación de la estrategia
    - Código: función de creación de features
    - Tabla: top 10 features creadas con descripción

CELDA 7 (Markdown + Code): Validación
    - Texto: justificación del split elegido
    - Código: train_test_split
    - print distribución de train y val

CELDA 8 (Markdown + Code): Modelado
    - Código: entrenar 4-6 modelos con fallback si alguna libreria no esta instalada
    - Tabla de resultados con todas las métricas
    - Conclusión: "Modelo X ganó con ROC-AUC Y y menor overfitting"

CELDA 9 (Markdown + Code): Evaluación del mejor modelo
    - Curva ROC (todos los modelos superpuestos)
    - Curva Precision-Recall
    - Análisis de threshold
    - Matriz de confusión
    - Lift chart por deciles

CELDA 10 (Markdown + Code): Interpretabilidad
    - Feature importance top 20
    - SHAP summary (bar + beeswarm)
    - Perfil del cliente en riesgo

CELDA 11 (Markdown + Code): Impacto de negocio
    - Definir supuestos como constantes (CLV, costo, efectividad)
    - Calcular beneficio/costo/ROI por threshold
    - Gráfico de ROI por threshold
    - Marcar CLARAMENTE con [SUPUESTO]

CELDA 12 (Markdown): Conclusiones y recomendaciones
    - 5 conclusiones técnicas
    - 5 recomendaciones para el banco
    - 3 limitaciones
    - 3 próximos pasos

CELDA 13 (Code): Guardar outputs
    - Guardar modelo con joblib
    - Exportar predicciones a CSV
    - print("Pipeline completado exitosamente")
```

### Criterios de calidad del notebook

- **DEBE** correr con `Kernel → Restart & Run All` sin errores.
- Cada sección de código va seguida de un markdown con conclusión.
- Todos los gráficos usan dark mode con la paleta definida.
- No hay celdas vacías ni outputs de debug.
- El notebook es legible para alguien que no escribió el código.
- Tiempo de ejecución total < 5 minutos.

---

### 5.2 Estructura de la PPT (10 slides)

| # | Slide | Contenido clave | Tiempo en exposición |
|---|---|---|---|
| 1 | **Portada** | Título impactante, equipo, fecha | 15 seg |
| 2 | **El Problema** | Tasa del evento + dato de impacto económico | 45 seg |
| 3 | **Insight del EDA** | El hallazgo más sorprendente (1 gráfico potente) | 45 seg |
| 4 | **Nuestra Estrategia** | 3 diferenciadores: validación, features, negocio | 30 seg |
| 5 | **Pipeline** | Diagrama: Datos → EDA → Features → Modelo → Score | 30 seg |
| 6 | **Resultados** | Tabla comparativa + métricas clave (AUC, F1, KS) | 60 seg |
| 7 | **Cliente en Riesgo** | Perfil visual + SHAP + reglas de negocio | 45 seg |
| 8 | **Modelo en Producción** | Mockup de dashboard + threshold recomendado | 30 seg |
| 9 | **Impacto Financiero** | ROI estimado + tabla de sensibilidad [SUPUESTOS] | 45 seg |
| 10 | **Cierre** | 3 bullets de conclusión + contacto + agradecimiento | 15 seg |

**Total: ~6 minutos** (ajustar según tiempo asignado)

---

### 5.3 Prompt para Gamma/Canva/PowerPoint AI

```
Diseña una presentación ejecutiva de 10 diapositivas para una datathon de banca.
Tema: predicción de [TIPO_PROBLEMA] de clientes bancarios.
Audiencia: jurado de ejecutivos de banca y ciencia de datos.

ESTILO VISUAL:
- Paleta: azul marino (#0A1628) + dorado (#F5A623) + blanco
- Tipografía: sans-serif moderna (Inter o Poppins), títulos grandes
- Estilo: glassmorphism sutil, dark mode, espacio en blanco generoso
- Gráficos: dark mode con alto contraste
- No usar párrafos. Usar bullets, números y stat cards.

ESTRUCTURA:
Slide 1: Portada con título impactante
Slide 2: El problema de negocio (stat card con % de evento + dato de costo)
Slide 3: Insight del EDA (placeholder para gráfico)
Slide 4: Estrategia diferenciadora (3 columnas con iconos)
Slide 5: Pipeline de solución (diagrama horizontal)
Slide 6: Resultados del modelo (3 stat cards + curva ROC placeholder)
Slide 7: Perfil del cliente en riesgo (avatar + características)
Slide 8: Cómo se usaría en producción (mockup dashboard)
Slide 9: Impacto financiero estimado (número grande de ROI)
Slide 10: Cierre con 3 bullets + contacto

Formato: .pptx, 16:9, dark mode.
```

---

### 5.4 Prompt para Codex (notebook)

```
Eres un Data Scientist Senior creando el notebook de entrega para una datathon bancaria.

CONTEXTO:
- El pipeline está en src/pipeline.py
- Los resultados están en reports/ (experiment_log.csv, threshold_analysis.csv, etc.)
- El modelo ganador está en models/best_model.joblib
- Los gráficos están en reports/figures/ (en dark mode)
- El dataset original es [NOMBRE_ARCHIVO] ([N] filas × [M] columnas)
- Target: [TARGET_COL] (0/1), tasa: [X]%

TU TAREA:
Crear notebooks/ENTREGA_DATATHON.ipynb — un notebook Jupyter limpio, profesional y
100% reproducible que sea el entregable principal al jurado.

El notebook debe:
1. Correr de inicio a fin sin errores (Restart & Run All)
2. Contener todo el pipeline: carga → EDA → features → validación → modelos → evaluación → SHAP → negocio
3. Cada sección tiene markdown con conclusión, no solo código
4. Gráficos en dark mode (fondo #0A1628, texto blanco, acento #F5A623)
5. Tabla comparativa de modelos con AUC, F1, KS, Lift, overfitting gap
6. Análisis de threshold con cálculo de ROI (con supuestos marcados como [SUPUESTO])
7. SHAP importance + beeswarm del mejor modelo
8. Conclusiones orientadas al negocio, no solo técnicas
9. Tiempo total < 5 minutos

NO hagas:
- No inventes datos o métricas
- No uses variables con leakage
- No apliques SMOTE/escalado/encoding antes del split
- No dejes celdas sin ejecutar o con errores
- No uses gráficos con fondo blanco
```

---

### 5.5 README.md del proyecto

```markdown
# 🏦 Datathon — [Título del Problema]
**[Universidad/Institución] | [Nombre del Equipo] | [Fecha]**

## Descripción del Problema
[2-3 párrafos sobre el problema y el objetivo]

## Resultados
| Métrica | Valor |
|---|---|
| Modelo ganador | [Nombre] |
| ROC-AUC | [X] |
| F1-Score | [X] |
| Lift Top 10% | [X]x |
| Overfitting gap | [X] |

## Estructura del Proyecto
[Árbol de directorios con descripción]

## Cómo Reproducir
1. Instalar dependencias: `pip install -r requirements.txt`
2. Ejecutar pipeline: `python src/pipeline.py`
3. O abrir: `notebooks/ENTREGA_DATATHON.ipynb`

## Equipo
[Nombres y roles]
```

---

## FEEDBACK LOOPS — CUÁNDO VOLVER ATRÁS

### Loop 1: Modelo → EDA (mejorar features)

**Cuándo activar:**
- ROC-AUC < 0.80 después del primer entrenamiento completo.
- Las top 10 features por importancia son todas variables raw (sin ingeniería).
- Error analysis revela patrones sistemáticos en FN (clientes que se van pero no detectamos).

**Qué pedir al EDA:**
```python
feedback_modelo_a_eda = {
    'problema': 'AUC insuficiente (actual: X)',
    'top_features_actuales': ['var1', 'var2', ...],
    'patrones_en_errores': 'FN concentrados en clientes con [característica]',
    'features_sugeridas': [
        'ratio entre [var_A] y [var_B]',
        'tendencia de [grupo de variables]',
        'interacción entre [var_C] y [var_D]',
    ],
    'time_budget_minutes': 20,
}
```

### Loop 2: Threshold → Modelo (ajustar objetivo)

**Cuándo activar:**
- El ROI es negativo en todos los thresholds razonables.
- El recall es < 0.30 en el threshold de máximo F1.

**Qué hacer:**
1. Probar `class_weight` ajustado manualmente.
2. Probar SMOTE dentro del pipeline de entrenamiento.
3. Evaluar si la métrica correcta es PR-AUC en lugar de ROC-AUC.
4. Considerar optimización directa de la métrica de negocio (utilidad).

### Loop 3: Negocio → Modelo (cambiar enfoque)

**Cuándo activar:**
- El modelo predice bien pero el impacto financiero es bajo.
- El perfil del cliente en riesgo no es accionable.

**Qué hacer:**
1. Segmentar por rentabilidad y exposicion: no basta con predecir default, hay que decidir monto/limite.
2. Cambiar umbrales para equilibrar defaults evitados vs. buenos clientes rechazados.
3. Crear un score compuesto: probabilidad de default x exposicion esperada x margen.

---

## TIMING Y PRIORIZACIÓN

### Timeline real para 3 horas

| Fase | Minutos | Acumulado | Documento | Qué produce |
|---|---|---|---|---|
| 0. Setup + caso | 10 | 0:10 | Orquestador | Variables, target, archivos, split |
| 1. EDA express | 25 | 0:35 | Doc 1 | Calidad, nulos, outliers, leakage |
| 2. Features reproducibles | 20 | 0:55 | Doc 1 | `feature_builder.py` + `features.parquet` |
| 3. Modelado base/champion | 45 | 1:40 | Doc 2 | LogReg + arbol boosting + comparativa |
| 4. Calibracion + ROI | 25 | 2:05 | Doc 2 / Orquestador | Brier, Gini, KS, politica 3 bandas |
| 5. Submission + explicabilidad | 20 | 2:25 | Doc 2 | `submission.csv`, SHAP/importance |
| 6. Notebook + PPT | 30 | 2:55 | Orquestador | Notebook limpio + max 10 slides |
| 7. Buffer final | 5 | 3:00 | Equipo | Revisar nombres, correr envio, congelar |

**Nota operativa:** aunque haya internet disponible, no depender de descargas durante el reto. Usar internet solo para confirmar sintaxis, instalar algo ya conocido o buscar una referencia puntual; la ruta ganadora debe correr con librerias locales preparadas.

### Qué cortar si falta tiempo

| Prioridad | Item | ¿Se puede omitir? |
|---|---|---|
| 🔴 CRÍTICO | Modelo funcional con métricas | NUNCA |
| 🔴 CRÍTICO | Tabla comparativa de modelos | NUNCA |
| 🔴 CRÍTICO | Anti-leakage verificado | NUNCA |
| 🟡 ALTO | Feature engineering | Solo reducir cantidad |
| 🟡 ALTO | SHAP / interpretabilidad | Usar feature_importances_ nativo |
| 🟡 ALTO | Análisis de negocio (ROI) | Simplificar a 1 tabla |
| 🟢 MEDIO | Optuna tuning | Usar parámetros razonables fijos |
| 🟢 MEDIO | Error analysis | Omitir si falta tiempo |
| 🟡 ALTO | Calibración de probabilidades | Simplificar a sigmoid o Brier reportado |
| 🔵 BAJO | Dashboard interactivo | Omitir |
| 🔵 BAJO | Ensemble / stacking | Omitir |
| 🔵 BAJO | PDP / ICE plots | Omitir |

---

## CHECKLIST FINAL ANTES DE ENVIAR

### Notebook

- [ ] Corre con `Restart & Run All` sin errores.
- [ ] Cada gráfico tiene título y conclusión en texto.
- [ ] No hay outputs de debug (prints innecesarios).
- [ ] La tabla comparativa de modelos está presente.
- [ ] Las métricas oficiales están claramente reportadas.
- [ ] Los supuestos de negocio están marcados con `[SUPUESTO]`.
- [ ] Gráficos en dark mode, no estilo default.
- [ ] Tiempo de ejecución total < 5 minutos.

### Modelo

- [ ] Hay baseline (Dummy + LogReg) para comparar.
- [ ] El overfitting gap entre train y validación es < 0.05.
- [ ] No hay leakage (variables futuras excluidas).
- [ ] El threshold está justificado.
- [ ] Se compararon al menos 4 modelos, incluyendo un baseline y un boosting.
- [ ] random_state=42 en todos los procesos aleatorios.

### Análisis de negocio

- [ ] Se calculó ROI por threshold.
- [ ] Se definió perfil del cliente en riesgo.
- [ ] Se escribieron recomendaciones accionables.
- [ ] Todos los supuestos están marcados.

### PPT

- [ ] Empieza por el PROBLEMA de negocio, no por la técnica.
- [ ] Incluye el hallazgo más sorprendente del EDA.
- [ ] Tiene métricas claras (AUC, F1, KS, Lift).
- [ ] Tiene perfil del cliente en riesgo.
- [ ] Tiene impacto financiero estimado.
- [ ] No tiene más de 10 slides.

### Envío

- [ ] Archivos en el formato correcto.
- [ ] Enviado al email/plataforma correcta.
- [ ] Antes de la hora límite.
- [ ] Equipo ha revisado los entregables.

---

## REGLAS UNIVERSALES

1. **No inventar datos.** Todo número debe venir de los datos reales o estar marcado como `[SUPUESTO]`.
2. **No saltar pasos criticos sin documentarlo.** Anti-leakage, validacion, comparativa y entregables no se omiten; los pasos opcionales se pueden recortar segun el timeline.
3. **Reproducibilidad.** `random_state=42` en todo proceso aleatorio.
4. **Anti-leakage.** No aplicar preprocesamiento antes del split train/test.
5. **Dark mode.** Todos los gráficos usan paleta oscura profesional.
6. **Conclusiones.** Cada gráfico va seguido de una conclusión de negocio.
7. **Prioridad al jurado.** Optimizar para lo que el jurado evalúa, no para perfección técnica invisible.

---

> **"No gana quien prueba más modelos. Gana quien valida mejor, crea mejores variables, evita leakage y explica por qué su modelo toma mejores decisiones para el negocio."**

---

## ⚡ PROMPT CORTO DE ARRANQUE CUANDO LLEGUE LA DATA

> [!TIP]
> Copia y pega el siguiente prompt en una nueva sesión del asistente de IA en cuanto la data real del caso sea colocada en la carpeta `dataInicial/`. Esto activará automáticamente todo el plan orquestado paso a paso con los parámetros correctos.

```markdown
Activa el plan orquestador y ejecuta la Fase 0 (Extracción del Caso) y la Fase 1 (EDA) para el reto de FinanCrece S.A.
La data inicial está ubicada en la carpeta `dataInicial/`.
Los parámetros autoritativos son:
- Target: `default_90d`
- IDs a excluir: `['id_cliente']`
- Métrica oficial: `roc_auc`
- Estrategia de validación por defecto: `stratified_split`; cambiar a `temporal_split` solo si existe columna real de fecha/periodo confiable.
- Archivos de salida: Guardar todo en una carpeta estructurada aparte (ej. `resultados_datathon/` en el root del proyecto) para mantener dataInicial/ limpia y aislada.
- Tiempo real disponible: 3 horas. Priorizar modelo funcional, anti-leakage, ROI y `submission.csv`.

¡Procedamos paso a paso respetando los Gates de cada documento!
```
