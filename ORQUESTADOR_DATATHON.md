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

Este sistema esta optimizado para una datathon bancaria supervisada y su ruta ejecutable por defecto es `clasificacion_binaria` para fuga/churn. La Fase 0 puede detectar regresion, multiclase, ranking, clustering o anomalias, pero si el caso no es clasificacion binaria se debe adaptar el Doc 2 antes de entrenar: metricas, modelos, umbrales, gates y entregables no se ejecutan literalmente.

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
| Duración total disponible | 5.5 Horas de desarrollo | Presentación / Slides |
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
| Métrica secundaria recomendada | F1-Score |
| ¿Hay dataset de test separado sin target? | Sí (`clientes_prueba.csv` / 10K filas) |
| ¿Hay que generar archivo submission? | Sí |
| Formato del submission | Archivo CSV con columnas `id_cliente` y `prob_default` |

---

### 0.5 Datos disponibles

| Archivo | Formato | Tamaño | Filas estimadas | Columnas | Descripción |
|---|---|---|---|---|---|
| `clientes_entrenamiento.csv` | .csv | ~6.0 MB | 40,000 | 18 | Dataset histórico con target real `default_90d` |
| `clientes_prueba.csv` | .csv | ~1.5 MB | 10,000 | 17 | Dataset de prueba cronológico (primer trimestre 2026) sin target |

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
- Período de los datos: Solicitudes históricas 2022 - 2024 (Train) vs. Primer Trimestre de 2026 (Test)
- ¿Es snapshot único o serie temporal?: Serie temporal implícita (solicitudes chronológicas)
- Tamaño del universo de clientes: 50,000 registros
- Tasa del evento (si se menciona): 22% de tasa de default aproximada en train
- ¿Datos anonimizados?: Sí, IDs codificados
- ¿Hay información de productos financieros?: Líneas de crédito y saldo deudor general
- ¿Hay información transaccional/de canales?: Sí, canal de captación de solicitudes
- ¿Hay información crediticia?: Historial de mora previo, consultas central y buró
- ¿Hay información demográfica?: Edad y zona geográfica de procedencia
- ¿Hay variables de rentabilidad?: Ingresos y ratios de endeudamiento
- Costo de adquisición vs retención (si se menciona): Pérdida promedio por default = $3,000 USD vs. Ganancia neta = $450 USD. Costo de rechazo erróneo (FP) = $150 USD.
- ¿Se mencionan campañas de retención/cobranza actuales?: No se mencionan campañas activas, requiere política desde cero.
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
    'data_paths': ['dataInicial/clientes_entrenamiento.csv'],
    'id_cols': ['id_cliente'],           # excluir identificadores
    'date_cols': [],                      # fechas conocidas
    'periodo_col': None,
    'group_col': None,
    'validation_strategy': 'temporal_split', # ideal para datos cronológicos 2022-2024 vs 2026
    'known_leakage_vars': [],
    'contexto_negocio': 'Scoring de Riesgo de Crédito para FinanCrece S.A. enfocándose en reducir mora del 7.8% al 4.2%.',
    'drop_cols': [],
    'restricciones': ['solo usar variables provistas'],
    'test_raw_path': 'dataInicial/clientes_prueba.csv',
    'submission_spec': {'cols': ['id_cliente', 'prob_default'], 'format': 'csv'},
    'priority_analysis': ['score_buro', 'ingreso_mensual', 'ratio_endeudamiento'],
    'random_state': 42,
    'time_budget_minutes': 45,           # reducidos bajo el budget de 5.5 horas
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

- [ ] ¿Se entrenaron mínimo 5 modelos (Dummy, LogReg, RF, LightGBM/XGBoost, CatBoost)?
- [ ] ¿Hay tabla comparativa con métricas consistentes?
- [ ] ¿El overfitting gap del mejor modelo es < 0.05?
- [ ] ¿Se optimizó el threshold?
- [ ] ¿Se calculó SHAP o feature importance?
- [ ] ¿Se guardaron todos los artefactos?

---

## FASE 3 — VERIFICACIÓN DE EXCELENCIA

### 3.1 Umbrales de excelencia por tipo de problema

#### Churn Bancario

| Métrica | Mediocre | Aceptable | Bueno | Excelente | Sospechoso |
|---|---|---|---|---|---|
| ROC-AUC | < 0.70 | 0.70 – 0.80 | 0.80 – 0.87 | 0.87 – 0.95 | > 0.95 |
| PR-AUC | < 0.25 | 0.25 – 0.40 | 0.40 – 0.55 | 0.55 – 0.70 | > 0.80 |
| F1-Score | < 0.35 | 0.35 – 0.50 | 0.50 – 0.60 | 0.60 – 0.75 | > 0.85 |
| KS Statistic | < 0.30 | 0.30 – 0.45 | 0.45 – 0.55 | 0.55 – 0.65 | > 0.70 |
| Lift Top 10% | < 2.0x | 2.0 – 3.0x | 3.0 – 4.0x | 4.0 – 5.5x | > 6.0x |
| Overfitting gap | > 0.08 | 0.05 – 0.08 | 0.03 – 0.05 | < 0.03 | — |

#### Fraude Bancario

| Métrica | Mediocre | Aceptable | Bueno | Excelente | Sospechoso |
|---|---|---|---|---|---|
| ROC-AUC | < 0.80 | 0.80 – 0.88 | 0.88 – 0.93 | 0.93 – 0.98 | > 0.99 |
| PR-AUC | < 0.15 | 0.15 – 0.35 | 0.35 – 0.55 | 0.55 – 0.75 | > 0.85 |
| Recall | < 0.50 | 0.50 – 0.70 | 0.70 – 0.85 | 0.85 – 0.95 | > 0.98 |

#### Default / Riesgo Crediticio

| Métrica | Mediocre | Aceptable | Bueno | Excelente | Sospechoso |
|---|---|---|---|---|---|
| ROC-AUC | < 0.65 | 0.65 – 0.75 | 0.75 – 0.83 | 0.83 – 0.92 | > 0.95 |
| Gini | < 0.30 | 0.30 – 0.50 | 0.50 – 0.66 | 0.66 – 0.84 | > 0.90 |
| KS | < 0.25 | 0.25 – 0.40 | 0.40 – 0.50 | 0.50 – 0.60 | > 0.65 |

#### Regresión (monto, saldo, ingreso)

| Métrica | Mediocre | Aceptable | Bueno | Excelente | Sospechoso |
|---|---|---|---|---|---|
| R² | < 0.30 | 0.30 – 0.55 | 0.55 – 0.75 | 0.75 – 0.90 | > 0.95 |
| MAPE | > 40% | 20% – 40% | 10% – 20% | 5% – 10% | < 2% |

---

### 3.2 Árbol de diagnóstico y acción

```
¿ROC-AUC > 0.85?
├── SÍ → ¿Overfitting gap < 0.05?
│   ├── SÍ → ✅ EXCELENTE. Continuar a Fase 4.
│   └── NO → Regularizar: reducir depth, aumentar min_samples, early stopping.
│           Volver a Fase 2 con restricciones.
└── NO → ¿ROC-AUC > 0.80?
    ├── SÍ → BUENO pero no excelente.
    │       Intentar:
    │       1. Optuna para hiperparámetros (30-50 trials)
    │       2. Más features de ingeniería → volver a Doc 1
    │       3. Ensemble (stacking LightGBM + CatBoost)
    │       4. Probar SMOTE o class_weight ajustado
    └── NO → ¿ROC-AUC > 0.70?
        ├── SÍ → ACEPTABLE pero necesita mejora.
        │       Diagnóstico:
        │       - ¿Las top features son todas raw? → crear más features
        │       - ¿Hay leakage inverso (variables que confunden)? → revisar
        │       - ¿El target está bien definido? → verificar
        │       Volver a Doc 1 con instrucciones específicas.
        └── NO → PROBLEMA SERIO.
                Verificar:
                - ¿El target es correcto?
                - ¿Hay fuga de datos en sentido contrario?
                - ¿Las variables tienen poder predictivo?
                - ¿El problema es realmente predecible?
                Escalar: revisar entendimiento del caso.
```

---

### 3.3 Protocolo de mejora iterativa

Si las métricas no son excelentes, iterar con este protocolo:

| Iteración | Acción | Tiempo máximo | Criterio de salida |
|---|---|---|---|
| 1 | Feature engineering adicional (Doc 1) | 30 min | +0.02 AUC o +0.05 F1 |
| 2 | Optuna hyperparameter search (Doc 2) | 20 min | +0.01 AUC |
| 3 | Ensemble stacking (Doc 2) | 15 min | +0.005 AUC |
| 4 | Revisión de leakage y variables (Doc 1) | 15 min | Confirmar limpieza |

**Regla de corte:** Si después de 2 iteraciones no hay mejora, aceptar el mejor modelo y enfocarse en presentación y negocio. El jurado valora más una solución bien explicada que un AUC marginalmente mayor.

---

## FASE 4 — ANÁLISIS DE NEGOCIO

### 4.1 Framework de impacto financiero

#### Parámetros base (marcar como `[SUPUESTO]` si no vienen del caso)

```python
# === PARÁMETROS DE NEGOCIO ===
# Marcar con [SUPUESTO] todo lo que no viene de los datos reales

CLV_ANUAL = 1500          # [SUPUESTO] Valor anual por cliente retenido (USD)
COSTO_CONTACTO = 25       # [SUPUESTO] Costo de contactar 1 cliente (USD)
TASA_EFECTIVIDAD = 0.15   # [SUPUESTO] % de clientes que responden a la campaña
COSTO_ADQUISICION = 500   # [SUPUESTO] Costo de adquirir un nuevo cliente (USD)
HORIZONTE_MESES = 12      # Horizonte de cálculo
```

#### Cálculo de ROI por threshold

```python
import numpy as np
import pandas as pd

def calcular_roi_por_threshold(y_true, y_proba, thresholds,
                                clv=1500, costo_contacto=25,
                                tasa_efectividad=0.15):
    """Calcula ROI de campaña de retención por threshold."""
    resultados = []

    for t in thresholds:
        y_pred = (y_proba >= t).astype(int)

        tp = ((y_pred == 1) & (y_true == 1)).sum()
        fp = ((y_pred == 1) & (y_true == 0)).sum()
        fn = ((y_pred == 0) & (y_true == 1)).sum()
        tn = ((y_pred == 0) & (y_true == 0)).sum()

        clientes_contactados = tp + fp
        clientes_salvados = tp * tasa_efectividad
        beneficio = clientes_salvados * clv
        costo = clientes_contactados * costo_contacto
        roi = (beneficio - costo) / max(costo, 1)
        beneficio_neto = beneficio - costo

        resultados.append({
            'threshold': round(t, 2),
            'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn,
            'contactados': clientes_contactados,
            'salvados_estimado': round(clientes_salvados, 1),
            'beneficio_usd': round(beneficio, 2),
            'costo_usd': round(costo, 2),
            'beneficio_neto_usd': round(beneficio_neto, 2),
            'roi': round(roi, 2),
        })

    return pd.DataFrame(resultados)
```

#### Matriz de costo-beneficio

```
┌──────────────────────────────────────────────────┐
│            PREDICHO POR EL MODELO                │
│                                                  │
│              Positivo         Negativo            │
│  Real  ┌──────────────┬──────────────────┐       │
│  Pos   │ TP: Cliente   │ FN: Cliente que  │       │
│  (fuga)│ salvado       │ se fue sin ser   │       │
│        │ +CLV×efect.   │ detectado        │       │
│        │               │ -CLV (pérdida)   │       │
│  ──────┼──────────────┼──────────────────┤       │
│  Neg   │ FP: Cliente   │ TN: Cliente que  │       │
│  (perm)│ contactado    │ se queda sin     │       │
│        │ innecesario   │ intervención     │       │
│        │ -costo_contac │ $0               │       │
│        └──────────────┴──────────────────┘       │
└──────────────────────────────────────────────────┘
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
1. **Activar campaña de retención** sobre el top X% de clientes con mayor score.
   - Contactar [N] clientes con probabilidad > [threshold].
   - Costo estimado: USD [X] | Beneficio esperado: USD [Y] | ROI: [Z]x
2. **Monitorear señales de alerta** identificadas por el modelo:
   - [Variable 1]: clientes con [comportamiento] tienen [X]x más riesgo.
   - [Variable 2]: [descripción del patrón].

### Acciones a mediano plazo (1-6 meses)
3. **Personalizar incentivos por segmento de rentabilidad:**
   - Clientes de alta rentabilidad + alto riesgo → intervención premium.
   - Clientes de baja rentabilidad + alto riesgo → evaluar costo-beneficio.
4. **Integrar el score con el CRM** para alertas automáticas a gestores comerciales.

### Acciones estratégicas (6-12 meses)
5. **Reentrenar el modelo mensualmente** con datos frescos.
6. **Implementar A/B testing** para medir impacto real de la campaña.
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
    - Código: entrenar 5-6 modelos
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
1. Segmentar por rentabilidad: solo predecir fuga de clientes valiosos.
2. Cambiar el threshold para priorizar precision (contactar menos pero mejor).
3. Crear un score compuesto: probabilidad × rentabilidad.

---

## TIMING Y PRIORIZACIÓN

### Timeline para datathon de 6 horas

| Fase | Minutos | Acumulado | Documento | Qué produce |
|---|---|---|---|---|
| 0. Caso | 20 | 0:20 | Orquestador | Comprensión total |
| 1. EDA | 80 | 1:40 | Doc 1 | 6-8 gráficos + features |
| 2. Modelado | 90 | 3:10 | Doc 2 | 5-6 modelos + evaluación |
| 3. Excelencia | 30 | 3:40 | Orquestador | Iteración si necesario |
| 4. Negocio | 30 | 4:10 | Orquestador | ROI + recomendaciones |
| 5. Notebook | 50 | 5:00 | Orquestador | .ipynb limpio |
| 6. PPT | 30 | 5:30 | Orquestador | Slides + prompt |
| 7. Buffer | 30 | 6:00 | — | Revisión y envío |

### Timeline para datathon de 24 horas

| Fase | Horas | Documento |
|---|---|---|
| 0. Caso + investigación del dominio | 1.5 | Orquestador |
| 1. EDA profundo | 3.0 | Doc 1 |
| 2. Feature engineering extensivo | 2.0 | Doc 1 |
| 3. Modelado + CV completo | 4.0 | Doc 2 |
| 4. Optuna + ensemble | 3.0 | Doc 2 |
| 5. Evaluación + SHAP profundo | 2.0 | Doc 2 |
| 6. Análisis de negocio + dashboard | 2.0 | Orquestador |
| 7. Notebook pulido | 2.0 | Orquestador |
| 8. PPT + ensayo de presentación | 2.0 | Orquestador |
| 9. Buffer / descanso | 2.5 | — |

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
| 🟢 MEDIO | Calibración de probabilidades | Omitir |
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
- [ ] Se compararon al menos 5 modelos.
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
- Estrategia de validación por defecto: `temporal_split` (evaluaremos estabilidad temporal de solicitudes 2022-2024 vs. 2026 de test).
- Archivos de salida: Guardar todo en una carpeta estructurada aparte (ej. `resultados_datathon/` en el root del proyecto) para mantener dataInicial/ limpia y aislada.

¡Procedamos paso a paso respetando los Gates de cada documento!
```

