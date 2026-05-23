# 🤖 Guía de Modelado, Validación y Evaluación — Sistema de Documentos para Datathon

> **Documento 2 de 3** | Se complementa con: `EDA_Guia_Datathon_Banca.md` (Doc 1) y `ORQUESTADOR_DATATHON.md` (Doc 3 — Flujo Principal)
>
> **Este documento se enfoca en el entrenamiento, validación rigurosa, optimización hiperparamétrica, evaluación de probabilidades, optimización del umbral de decisión, interpretabilidad y exportación reproducible.**

---

## 0. INTERFAZ CON EL EDA Y EL ORQUESTADOR

### 0.1 Entradas que este documento espera (INPUTS)

El EDA (`EDA_Guia_Datathon_Banca.md`) debe haber guardado los datos de features y el handoff en las siguientes rutas antes de iniciar. El camino ejecutable de este documento asume clasificacion binaria; si el Orquestador detecto otro tipo de problema, adaptar metricas, modelos y gates antes de correrlo.

| Recurso | Ruta Esperada | Descripción |
|---|---|---|
| Dataset de features | `data/processed/features.parquet` | Features pre-split; puede contener nulos para tratar en pipeline |
| Resumen del EDA | `reports/eda_summary.csv` | Listado de variables con su tipo y correlación inicial |
| Metadatos del EDA | `reports/eda_handoff.json` | JSON con la tasa del evento, target_col, id_cols, etc. |
| Feature builder | `src/feature_builder.py` | Requerido si se generara submission desde test raw |

```python
# --- BLOQUE DE CONFIGURACIÓN (Heredado del Orquestador/EDA) ---
from pathlib import Path
import json

PROJECT_ROOT = Path(".")

# Cargar metadatos del handoff del EDA
with open(PROJECT_ROOT / "reports" / "eda_handoff.json", "r") as f:
    eda_handoff = json.load(f)

if eda_handoff["status"] != "READY":
    raise ValueError("EDA handoff bloqueado. Resolver gates del Doc 1 antes de modelar.")

TARGET_COL          = eda_handoff["target_col"]
ID_COLS             = eda_handoff["id_cols"]
METRICA_JURADO      = eda_handoff["metrica_jurado"]
TIPO_PROBLEMA       = eda_handoff["tipo_problema"]
VALIDATION_STRATEGY = eda_handoff.get("validation_strategy", "stratified_split")
FEATURE_BUILDER_PATH = eda_handoff.get("feature_builder_path")
RANDOM_STATE        = 42

if TIPO_PROBLEMA != "clasificacion_binaria":
    raise ValueError("Doc 2 requiere adaptar modelos/gates antes de salir de clasificacion_binaria.")
```

**Frontera con Doc 1:** este documento recibe features reproducibles y decisiones de leakage. A partir de aqui el split ocurre antes de cualquier `fit` de imputadores, encoders, escaladores, calibradores o transformaciones aprendidas.

### 0.2 Salidas que este documento produce (OUTPUTS)

| Artefacto | Ruta | Descripción |
|---|---|---|
| Modelo serializado | `models/best_model.joblib` | Modelo campeón entrenado |
| Pipeline preprocessor | `models/preprocessor.joblib` | Pipeline de preprocesamiento de sklearn/custom |
| Parámetros y metadata | `models/model_metadata.json` | Métricas finales, hiperparámetros y orden de features |
| Log de experimentos | `reports/experiment_log.csv` | Registro de métricas comparativas de todos los modelos entrenados |
| Análisis de threshold | `reports/threshold_analysis.csv` | Métricas de negocio y estadísticas por umbral de decisión |
| Política de 3 bandas | `reports/politica_3_bandas.csv` | Umbrales bajo/medio/alto y beneficio esperado |
| Feature Importance | `reports/feature_importance.csv` | Ranking final de variables del modelo ganador |
| Predicciones de val | `reports/predicciones_validacion.csv` | Scores probabilísticos y reales para análisis de errores |
| Curvas de evaluación | `reports/figures/model_evaluation_curves.png` | Panel con curvas ROC, PR, Confusión y Lift en Dark Mode |
| Curva de calibración | `reports/figures/calibration_curve.png` | Revisión visual de confiabilidad de `prob_default` |
| Resumen de SHAP | `reports/figures/shap_summary.png` | Gráfico beeswarm si el campeon es compatible con SHAP |

### 0.3 Condiciones de puerta (GATE CONDITIONS)

El proceso de modelado **NO se considera finalizado** hasta cumplir **todas** estas condiciones:

```python
GATE_CONDITIONS = {
    "modelos_minimos_entrenados": False,  # >=4 modelos: Dummy, LogReg, RF y al menos un boosting; >=5 si hay librerias
    "overfitting_bajo":         False,  # Diferencia de métrica oficial entre Train y Val < 0.05
    "metricas_credito_ok":      False,  # ROC-AUC >= 0.75, KS >= 0.30 y Gini >= 0.50 para scoring crediticio competitivo
    "calibracion_revisada":     False,  # Brier/calibracion evaluados antes de usar prob_default
    "threshold_optimizado":     False,  # Threshold y 3 bandas basados en ROI crediticio
    "interpretabilidad_exportada": False,  # SHAP o feature importance exportada
    "entregables_exportados":   False,  # Modelo, preprocessor y metadata guardados en models/
}

def verificar_gate_modelo():
    pendientes = [k for k, v in GATE_CONDITIONS.items() if not v]
    if pendientes:
        print(f"⛔ GATE DE MODELADO BLOQUEADO — Pendientes: {pendientes}")
        return False
    print("✅ GATE DE MODELADO APROBADO — Listo para Análisis de Negocio y Presentación")
    return True
```

---

## 1. ESTILO GRÁFICO BANCARIO (DARK MODE)

Para mantener una consistencia visual de alto nivel que impresione al jurado en la presentación y el notebook, configuramos un estilo premium basado en una paleta corporativa oscura (azul marino profundo + dorado + azul brillante).

```python
import matplotlib.pyplot as plt
import seaborn as sns

def aplicar_estilo_grafico():
    """Configura matplotlib y seaborn con un estilo dark-mode corporativo bancario."""
    plt.style.use("dark_background")
    plt.rcParams.update({
        "figure.facecolor":  "#0A1628", # Azul marino ultra oscuro
        "axes.facecolor":    "#0A1628",
        "text.color":        "#FFFFFF",
        "axes.labelcolor":   "#FFFFFF",
        "xtick.color":       "#FFFFFF",
        "ytick.color":       "#FFFFFF",
        "grid.color":        "#1C2D42", # Rejilla sutil
        "font.family":       "sans-serif",
        "font.size":         11,
        "axes.titlesize":    14,
        "axes.labelsize":    12,
        "legend.fontsize":   10,
        "savefig.facecolor": "#0A1628",
    })
    
PALETTE_BANCO = {
    "pos":      "#F5A623",  # Dorado / Fuga / Riesgo (Clase 1)
    "neg":      "#2D6DB5",  # Azul eléctrico / Permanencia / Seguro (Clase 0)
    "accent":   "#00E5FF",  # Cian brillante para acentos
    "neutral":  "#A0AEC0",  # Gris para elementos secundarios
    "bg":       "#0A1628",
    "grid":     "#1C2D42"
}

aplicar_estilo_grafico()
```

---

## 2. LAS 12 FASES DEL MODELADO

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              FLUJO DE MODELADO DE EXCELENCIA                           │
│                                                                                        │
│  [FASE 1] Carga y Definición del Problema                                              │
│      └─ [FASE 2] Partición de Datos (Anti-Leakage)                                      │
│             └─ [FASE 3] Pipeline de Preprocesamiento                                    │
│                    └─ [FASE 4] Entrenar Baselines (Dummy/LogReg)                       │
│                           └─ [FASE 5] Entrenar Modelos Avanzados (Tree-Based)          │
│                                  └─ [FASE 6] Suite Completa de Evaluación (10 Métricas)│
│                                         └─ [FASE 7] Ajuste Fino con Optuna              │
│                                                └─ [FASE 8] Optimización de Threshold    │
│                                                       └─ [FASE 9] SHAP e Interpretab.  │
│                                                              └─ [FASE 10] Error Analysis│
│                                                                     └─ [FASE 11] Selecc.│
│                                                                            └─ [FASE 12] │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### FASE 1: Carga y Definición del Problema

Cargamos el dataset procesado por el EDA, validamos dtypes y confirmamos la distribución de clases.

```python
import pandas as pd
import numpy as np

# Carga de datos
data_path = PROJECT_ROOT / "data" / "processed" / "features.parquet"
df = pd.read_parquet(data_path)

print(f"📊 Dataset cargado: {df.shape[0]:,} filas × {df.shape[1]} columnas")

# Confirmación del Target
if TARGET_COL not in df.columns:
    raise ValueError(f"❌ La columna target '{TARGET_COL}' no existe en el dataset.")

target_counts = df[TARGET_COL].value_counts(dropna=False)
target_pct = df[TARGET_COL].value_counts(normalize=True) * 100

print(f"🎯 Distribución del Target ({TARGET_COL}):")
for val, count in target_counts.items():
    print(f"   Clase {val}: {count:,} ({target_pct[val]:.2f}%)")

# Separación de variables predictoras y exclusiones
X = df.drop(columns=[TARGET_COL] + ID_COLS, errors="ignore")
y = df[TARGET_COL]

print(f"📝 Variables predictoras iniciales: {X.shape[1]}")
```

---

### FASE 2: Partición de Datos (Estrategia de Validación Anti-Leakage)

> [!IMPORTANT]
> **REGLA CARDINAL DE LA VALIDACIÓN:** El split de datos debe simular perfectamente cómo operará el modelo en producción. Nunca debe haber mezcla de información temporal o de grupos repetidos.

Utilizamos la estrategia decidida por el Orquestador:

```python
from sklearn.model_selection import train_test_split, StratifiedKFold

# Si el Orquestador pide temporal_split pero no hay una columna cronologica real,
# se cae de forma segura a stratified_split para evitar una falsa validacion temporal.
if VALIDATION_STRATEGY == "temporal_split":
    periodo_col_check = eda_handoff.get("periodo_col")
    if not periodo_col_check or periodo_col_check not in df.columns:
        print("⚠️ temporal_split solicitado sin columna de periodo valida; usando stratified_split anti-leakage.")
        VALIDATION_STRATEGY = "stratified_split"

# 1. SPLIT ESTRATIFICADO CLÁSICO (Sin fuerte componente temporal)
if VALIDATION_STRATEGY == "stratified_split":
    # Separamos 20% para test final (intocable hasta el final)
    X_train_full, X_test, y_train_full, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_STATE, stratify=y
    )
    # Separamos validación (20% del total)
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_full, y_train_full, test_size=0.25, random_state=RANDOM_STATE, stratify=y_train_full
    )
    print(f"✅ Validación cruzada: Stratified Split 60/20/20")

# 2. SPLIT TEMPORAL (Cuando hay variable de período o fecha)
elif VALIDATION_STRATEGY == "temporal_split":
    periodo_col = eda_handoff.get("periodo_col")
    if not periodo_col or periodo_col not in df.columns:
        raise ValueError(f"❌ Se especificó temporal_split pero no existe la columna de periodo '{periodo_col}'")
        
    periodos = sorted(df[periodo_col].unique())
    n_periodos = len(periodos)
    
    # Entrenamos con los primeros periodos, validamos con el penúltimo, testeamos con el último
    train_periods = periodos[:-2]
    val_periods = [periodos[-2]]
    test_periods = [periodos[-1]]
    
    train_mask = df[periodo_col].isin(train_periods)
    val_mask = df[periodo_col].isin(val_periods)
    test_mask = df[periodo_col].isin(test_periods)
    
    X_train, y_train = X[train_mask], y[train_mask]
    X_val, y_val = X[val_mask], y[val_mask]
    X_test, y_test = X[test_mask], y[test_mask]
    
    print(f"📅 Split Temporal:")
    print(f"   Train: {train_periods} (Filas: {X_train.shape[0]:,})")
    print(f"   Val:   {val_periods} (Filas: {X_val.shape[0]:,})")
    print(f"   Test:  {test_periods} (Filas: {X_test.shape[0]:,})")

# 3. SPLIT POR GRUPOS (Múltiples filas por cliente)
elif VALIDATION_STRATEGY == "group_split":
    group_col = eda_handoff.get("group_col")
    if not group_col or group_col not in df.columns:
        raise ValueError(f"❌ Se especificó group_split pero no existe la columna de grupo '{group_col}'")
        
    from sklearn.model_selection import GroupShuffleSplit
    gss1 = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=RANDOM_STATE)
    train_idx, test_idx = next(gss1.split(X, y, groups=df[group_col]))
    
    X_train_full, y_train_full = X.iloc[train_idx], y.iloc[train_idx]
    groups_train_full = df[group_col].iloc[train_idx]
    X_test, y_test = X.iloc[test_idx], y.iloc[test_idx]
    
    gss2 = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=RANDOM_STATE)
    train_sub_idx, val_idx = next(gss2.split(X_train_full, y_train_full, groups=groups_train_full))
    
    X_train, y_train = X_train_full.iloc[train_sub_idx], y_train_full.iloc[train_sub_idx]
    X_val, y_val = X_train_full.iloc[val_idx], y_train_full.iloc[val_idx]
    print(f"👥 Group Split por '{group_col}' 60/20/20")

print(f"   Train Shape: {X_train.shape}")
print(f"   Val Shape:   {X_val.shape}")
print(f"   Test Shape:  {X_test.shape}")
```

---

### FASE 3: Pipeline de Preprocesamiento

> [!CAUTION]
> **PREVENCIÓN DE LEAKAGE EXTREMA:** Todo ajuste (`.fit()`) del preprocesador se debe hacer **exclusivamente con los datos de entrenamiento**. Los sets de validación y test solo deben transformarse (`.transform()`).

Separamos las variables numéricas y categóricas para construir un pipeline robusto usando `ColumnTransformer`.

```python
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler, RobustScaler
from sklearn.impute import SimpleImputer

# Identificar tipos de variables
num_cols = X_train.select_dtypes(include=["int64", "float64"]).columns.tolist()
cat_cols = X_train.select_dtypes(include=["object", "category", "bool"]).columns.tolist()

print(f"   Numéricas: {len(num_cols)} | Categóricas: {len(cat_cols)}")

# Pipeline Numérico: Imputación con Mediana + Escalador robusto (evita problemas con outliers)
num_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", RobustScaler())
])

# Pipeline Categórico: Imputación con 'Desconocido' + One-Hot Encoding
# Evita errores con categorías nuevas en test usando handle_unknown='ignore'
cat_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="constant", fill_value="Desconocido")),
    ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
])

# Ensamblar preprocesador
preprocessor = ColumnTransformer(
    transformers=[
        ("num", num_transformer, num_cols),
        ("cat", cat_transformer, cat_cols)
    ],
    remainder="passthrough" # Pasa features binarias o preprocesadas que no requieran cambio
)

# Ajustar y transformar en Train, transformar en Val/Test
X_train_proc = preprocessor.fit_transform(X_train)
X_val_proc   = preprocessor.transform(X_val)
X_test_proc  = preprocessor.transform(X_test)

# Obtener nombres de columnas resultantes del preprocesamiento
cat_encoder = preprocessor.named_transformers_["cat"].named_steps["encoder"]
encoded_cat_cols = cat_encoder.get_feature_names_out(cat_cols).tolist() if cat_cols else []
feature_names_out = num_cols + encoded_cat_cols

print(f"✅ Datos preprocesados. Features resultantes: {len(feature_names_out)}")
```

---

### FASE 4: Entrenar Modelos Baselines (Dummy y Regresión Logística)

Para validar si nuestro modelo realmente aporta valor, necesitamos comparar contra baselines simples.

```python
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

# 1. Dummy Classifier (Predicción aleatoria proporcional a clase)
dummy_model = DummyClassifier(strategy="stratified", random_state=RANDOM_STATE)
dummy_model.fit(X_train_proc, y_train)

# 2. Regresión Logística (Muestra linealidad de variables)
# Usamos class_weight='balanced' debido al desbalance bancario típico
log_reg = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1)
log_reg.fit(X_train_proc, y_train)

print("✅ Baselines entrenados exitosamente.")
```

---

### FASE 5: Entrenar Modelos Avanzados (Tree-Based & Boosting)

Entrenamos algoritmos fuertes para datos tabulares: **Random Forest, LightGBM, XGBoost y CatBoost** cuando esten disponibles. Si alguna libreria no esta instalada, el flujo usa `HistGradientBoostingClassifier` como fallback para mantener una ruta ejecutable en 3 horas.

```python
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier

try:
    import lightgbm as lgb
except ImportError:
    lgb = None
    print("⚠️ LightGBM no disponible; se usara fallback sklearn si hace falta.")

try:
    import xgboost as xgb
except ImportError:
    xgb = None
    print("⚠️ XGBoost no disponible; continuar sin este candidato.")

try:
    from catboost import CatBoostClassifier
except ImportError:
    CatBoostClassifier = None
    print("⚠️ CatBoost no disponible; continuar sin este candidato.")

# Ajustar pesos de clase para desbalance
pos_weight = (len(y_train) - sum(y_train)) / sum(y_train)

# 1. Random Forest
rf_model = RandomForestClassifier(
    n_estimators=300,
    max_depth=10,
    class_weight="balanced",
    random_state=RANDOM_STATE,
    n_jobs=-1
)
rf_model.fit(X_train_proc, y_train)

modelos_avanzados = [(rf_model, "Random Forest")]

# 2. LightGBM (clave en datathons por velocidad) o fallback sklearn
if lgb is not None:
    lgb_model = lgb.LGBMClassifier(
        n_estimators=500,
        learning_rate=0.03,
        max_depth=6,
        num_leaves=31,
        scale_pos_weight=pos_weight,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbosity=-1
    )
    lgb_model.fit(
        X_train_proc, y_train,
        eval_set=[(X_val_proc, y_val)],
        callbacks=[lgb.early_stopping(50, verbose=False)]
    )
    modelos_avanzados.append((lgb_model, "LightGBM"))
else:
    hgb_model = HistGradientBoostingClassifier(
        max_iter=300,
        learning_rate=0.05,
        max_leaf_nodes=31,
        random_state=RANDOM_STATE,
    )
    hgb_model.fit(X_train_proc, y_train)
    modelos_avanzados.append((hgb_model, "HistGradientBoosting"))

# 3. XGBoost
if xgb is not None:
    xgb_model = xgb.XGBClassifier(
        n_estimators=500,
        learning_rate=0.03,
        max_depth=6,
        scale_pos_weight=pos_weight,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        eval_metric="logloss"
    )
    xgb_model.fit(
        X_train_proc, y_train,
        eval_set=[(X_val_proc, y_val)],
        verbose=False
    )
    modelos_avanzados.append((xgb_model, "XGBoost"))

# 4. CatBoost
if CatBoostClassifier is not None:
    cat_model = CatBoostClassifier(
        iterations=600,
        learning_rate=0.04,
        depth=6,
        auto_class_weights="Balanced",
        random_state=RANDOM_STATE,
        verbose=False
    )
    cat_model.fit(
        X_train_proc, y_train,
        eval_set=(X_val_proc, y_val),
        early_stopping_rounds=50,
        verbose=False
    )
    modelos_avanzados.append((cat_model, "CatBoost"))

print(f"✅ Modelos avanzados entrenados: {[nombre for _, nombre in modelos_avanzados]}")
```

---

### FASE 6: Suite Completa de Evaluación (10 Métricas Clave)

No nos limitamos al ROC-AUC. Evaluamos estabilidad, precisión en extremos y valor comercial.

```python
from sklearn.metrics import (
    roc_auc_score, precision_recall_curve, auc, f1_score,
    accuracy_score, precision_score, recall_score, log_loss,
    brier_score_loss, confusion_matrix
)

def calcular_ks_statistic(y_true, y_proba):
    """Calcula el estadístico Kolmogorov-Smirnov (KS)."""
    df_temp = pd.DataFrame({"real": y_true, "proba": y_proba})
    df_temp = df_temp.sort_values(by="proba", ascending=False)
    df_temp["cum_pos"] = (df_temp["real"] == 1).cumsum() / (df_temp["real"] == 1).sum()
    df_temp["cum_neg"] = (df_temp["real"] == 0).cumsum() / (df_temp["real"] == 0).sum()
    ks = (df_temp["cum_pos"] - df_temp["cum_neg"]).abs().max()
    return ks

def calcular_lift_top_10(y_true, y_proba):
    """Calcula el Lift acumulado en el top 10% de mayor score."""
    df_temp = pd.DataFrame({"real": y_true, "proba": y_proba})
    df_temp = df_temp.sort_values(by="proba", ascending=False)
    top_10_cutoff = int(len(df_temp) * 0.10)
    top_10 = df_temp.head(top_10_cutoff)
    tasa_top_10 = top_10["real"].mean()
    tasa_global = df_temp["real"].mean()
    lift = tasa_top_10 / max(tasa_global, 1e-5)
    return lift

def evaluar_modelo(modelo, X_t, y_t, X_v, y_v, nombre_modelo):
    """Genera suite de 10 métricas para train y validación."""
    y_proba_t = modelo.predict_proba(X_t)[:, 1]
    y_proba_v = modelo.predict_proba(X_v)[:, 1]
    
    # Clasificación por defecto (t=0.5)
    y_pred_t = (y_proba_t >= 0.5).astype(int)
    y_pred_v = (y_proba_v >= 0.5).astype(int)
    
    # PR-AUC
    p_t, r_t, _ = precision_recall_curve(y_t, y_proba_t)
    p_v, r_v, _ = precision_recall_curve(y_v, y_proba_v)
    pr_auc_t = auc(r_t, p_t)
    pr_auc_v = auc(r_v, p_v)
    
    metrics = {
        "Modelo":          nombre_modelo,
        "ROC-AUC Train":   round(roc_auc_score(y_t, y_proba_t), 4),
        "ROC-AUC Val":     round(roc_auc_score(y_v, y_proba_v), 4),
        "PR-AUC Val":      round(pr_auc_v, 4),
        "F1-Score Val":    round(f1_score(y_v, y_pred_v), 4),
        "Recall Val":      round(recall_score(y_v, y_pred_v), 4),
        "Precision Val":   round(precision_score(y_v, y_pred_v), 4),
        "KS Val":          round(calcular_ks_statistic(y_v, y_proba_v), 4),
        "Gini Val":        round(2 * roc_auc_score(y_v, y_proba_v) - 1, 4),
        "Lift@10% Val":    round(calcular_lift_top_10(y_v, y_proba_v), 2),
        "Brier Loss Val":  round(brier_score_loss(y_v, y_proba_v), 4),
        "Log Loss Val":    round(log_loss(y_v, y_proba_v), 4),
        "Overfitting Gap": round(abs(roc_auc_score(y_t, y_proba_t) - roc_auc_score(y_v, y_proba_v)), 4)
    }
    return metrics

# Evaluar todos los modelos
resultados = []
modelos = [
    (dummy_model, "Dummy Baseline"),
    (log_reg, "Logistic Regression"),
] + modelos_avanzados

for mod, nom in modelos:
    res = evaluar_modelo(mod, X_train_proc, y_train, X_val_proc, y_val, nom)
    resultados.append(res)

df_experimentos = pd.DataFrame(resultados)
df_experimentos.to_csv(PROJECT_ROOT / "reports" / "experiment_log.csv", index=False)

# El campeon se decide por la metrica oficial; CatBoost es candidato, no supuesto.
metricas_seleccion = {
    "roc_auc": "ROC-AUC Val",
    "pr_auc": "PR-AUC Val",
    "f1": "F1-Score Val",
}
metric_col = metricas_seleccion.get(METRICA_JURADO, "ROC-AUC Val")
modelos_por_nombre = {nom: mod for mod, nom in modelos}
best_result = df_experimentos.sort_values(metric_col, ascending=False).iloc[0]
best_name = best_result["Modelo"]
best_model = modelos_por_nombre[best_name]

# Visualizar tabla de experimentos
print("\n📋 LOG DE EXPERIMENTOS:")
print(df_experimentos[["Modelo", "ROC-AUC Train", "ROC-AUC Val", "PR-AUC Val", "F1-Score Val", "KS Val", "Overfitting Gap"]].to_markdown(index=False))
print(f"\n🏆 Campeon inicial por {metric_col}: {best_name}")
```

```python
# --- GENERACIÓN DE PANEL DE EVALUACIÓN GRÁFICA (DARK MODE) ---
import matplotlib.pyplot as plt
from sklearn.metrics import RocCurveDisplay, PrecisionRecallDisplay

def generar_panel_curvas(modelos, X_v, y_v, campeon, nombre_campeon):
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. Curvas ROC
    ax_roc = axes[0, 0]
    ax_roc.set_title("Curva ROC (Validación)", color=PALETTE_BANCO["accent"])
    for mod, nom in modelos:
        if nom == "Dummy Baseline": continue
        RocCurveDisplay.from_estimator(mod, X_v, y_v, name=nom, ax=ax_roc)
    ax_roc.plot([0, 1], [0, 1], linestyle="--", color=PALETTE_BANCO["neutral"])
    ax_roc.grid(True, color=PALETTE_BANCO["grid"])
    
    # 2. Curvas Precision-Recall (Vital con target desbalanceado)
    ax_pr = axes[0, 1]
    ax_pr.set_title("Curva Precision-Recall", color=PALETTE_BANCO["accent"])
    for mod, nom in modelos:
        if nom == "Dummy Baseline": continue
        PrecisionRecallDisplay.from_estimator(mod, X_v, y_v, name=nom, ax=ax_pr)
    ax_pr.grid(True, color=PALETTE_BANCO["grid"])
    
    # 3. Matriz de Confusion del campeon elegido por la metrica oficial
    ax_cm = axes[1, 0]
    ax_cm.set_title(f"Matriz de Confusion ({nombre_campeon})", color=PALETTE_BANCO["accent"])
    y_pred_campeon = (campeon.predict_proba(X_v)[:, 1] >= 0.5).astype(int)
    cm = confusion_matrix(y_v, y_pred_campeon)
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False, ax=ax_cm,
                xticklabels=["Permanece", "Fuga"], yticklabels=["Permanece", "Fuga"])
    ax_cm.set_xlabel("Predicho")
    ax_cm.set_ylabel("Real")
    
    # 4. Lift Chart Acumulado
    ax_lift = axes[1, 1]
    ax_lift.set_title("Gráfico de Lift Acumulado", color=PALETTE_BANCO["accent"])
    for mod, nom in modelos:
        if nom in ["Dummy Baseline", "Logistic Regression"]: continue
        prob = mod.predict_proba(X_v)[:, 1]
        df_l = pd.DataFrame({"real": y_v, "proba": prob}).sort_values("proba", ascending=False)
        df_l["decil"] = pd.qcut(range(len(df_l)), q=10, labels=False)
        tasa_global = df_l["real"].mean()
        lift_deciles = []
        for d in range(10):
            tasa_decil = df_l[df_l["decil"] <= d]["real"].mean()
            lift_deciles.append(tasa_decil / max(tasa_global, 1e-5))
        ax_lift.plot(range(1, 11), lift_deciles, marker="o", label=nom)
    ax_lift.set_xlabel("Deciles Acumulados")
    ax_lift.set_ylabel("Lift")
    ax_lift.legend()
    ax_lift.grid(True, color=PALETTE_BANCO["grid"])
    
    plt.tight_layout()
    plt.savefig(PROJECT_ROOT / "reports" / "figures" / "model_evaluation_curves.png", dpi=200)
    plt.close()

# Generar el panel grafico
generar_panel_curvas(modelos, X_val_proc, y_val, best_model, best_name)
```

---

### FASE 7: Ajuste Fino Ligero de Hiperparámetros

Con solo 3 horas, esta fase es opcional. Ejecutarla solo si el pipeline ya corre completo, la submission esta controlada y queda margen real. El bloque siguiente optimiza CatBoost con pocos trials; si otra familia lidera claramente, optimizar esa familia o documentar por que se mantiene el campeon actual.

```python
try:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
except ImportError:
    print("⚠️ Optuna no está instalado. Ejecute 'pip install optuna' para habilitar esta fase.")
    optuna = None

def optimizar_hyperparametros(X_tr, y_tr, X_va, y_va):
    if not optuna: return None
    if CatBoostClassifier is None:
        print("⚠️ CatBoost no disponible; se omite Optuna CatBoost.")
        return None
    
    def objective(trial):
        params = {
            "iterations":     trial.suggest_int("iterations", 300, 800),
            "learning_rate":  trial.suggest_float("learning_rate", 0.01, 0.1, log=True),
            "depth":          trial.suggest_int("depth", 4, 8),
            "l2_leaf_reg":    trial.suggest_float("l2_leaf_reg", 1e-3, 10.0, log=True),
            "border_count":   trial.suggest_int("border_count", 32, 255),
            "auto_class_weights": "Balanced",
            "random_seed":    RANDOM_STATE,
            "verbose":        False
        }
        
        trial_model = CatBoostClassifier(**params)
        trial_model.fit(X_tr, y_tr, eval_set=(X_va, y_va), early_stopping_rounds=30, verbose=False)
        preds = trial_model.predict_proba(X_va)[:, 1]
        
        if METRICA_JURADO == "pr_auc":
            precision, recall, _ = precision_recall_curve(y_va, preds)
            return auc(recall, precision)
        if METRICA_JURADO == "f1":
            return f1_score(y_va, (preds >= 0.5).astype(int))
        return roc_auc_score(y_va, preds)

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=10, timeout=900)
    
    print(f"🎯 Optuna: Mejor {METRICA_JURADO} = {study.best_value:.4f}")
    return study.best_params

# Ejecutar optimización
best_params = optimizar_hyperparametros(X_train_proc, y_train, X_val_proc, y_val)
if best_params:
    print(f"⚙️ Mejores parámetros encontrados: {best_params}")
    # Re-entrenar candidato CatBoost con los mejores parametros
    best_params["auto_class_weights"] = "Balanced"
    best_params["random_seed"] = RANDOM_STATE
    cat_model = CatBoostClassifier(**best_params)
    cat_model.fit(X_train_proc, y_train, eval_set=(X_val_proc, y_val), early_stopping_rounds=50, verbose=False)

    res_tuned = evaluar_modelo(
        cat_model, X_train_proc, y_train, X_val_proc, y_val, "CatBoost Optuna"
    )
    df_experimentos = pd.concat(
        [df_experimentos, pd.DataFrame([res_tuned])],
        ignore_index=True,
    )
    df_experimentos.to_csv(PROJECT_ROOT / "reports" / "experiment_log.csv", index=False)
    modelos_por_nombre["CatBoost Optuna"] = cat_model
    modelos.append((cat_model, "CatBoost Optuna"))
    if res_tuned[metric_col] >= best_result[metric_col]:
        best_result = pd.Series(res_tuned)
        best_name = "CatBoost Optuna"
        best_model = cat_model
        print(f"🏆 Nuevo campeon por {metric_col}: {best_name}")

    # Actualizar el panel si tuning agrego un candidato o cambio el campeon.
    generar_panel_curvas(modelos, X_val_proc, y_val, best_model, best_name)
```

---

### FASE 7.5: Calibración de Probabilidades

> [!IMPORTANT]
> Para scoring de crédito no basta ordenar bien a los clientes. Si se usará `prob_default` para aprobar, condicionar o rechazar, la probabilidad debe estar razonablemente calibrada.

```python
from sklearn.calibration import CalibratedClassifierCV, calibration_curve

def calibrar_probabilidades(modelo, X_cal, y_cal, metodo="sigmoid"):
    """
    Calibra el campeon con validacion. Idealmente se usa un set de calibracion separado;
    en datathon de 3 horas se permite usar validacion si se reporta la limitacion.
    """
    proba_raw = modelo.predict_proba(X_cal)[:, 1]
    brier_raw = brier_score_loss(y_cal, proba_raw)
    auc_raw = roc_auc_score(y_cal, proba_raw)

    try:
        calibrador = CalibratedClassifierCV(modelo, method=metodo, cv="prefit")
        calibrador.fit(X_cal, y_cal)
        proba_cal = calibrador.predict_proba(X_cal)[:, 1]

        brier_cal = brier_score_loss(y_cal, proba_cal)
        auc_cal = roc_auc_score(y_cal, proba_cal)

        usar_calibrado = (brier_cal <= brier_raw) and (auc_cal >= auc_raw - 0.01)
        modelo_final = calibrador if usar_calibrado else modelo
        proba_final = proba_cal if usar_calibrado else proba_raw
        estado = f"calibrated_{metodo}" if usar_calibrado else "raw_model_better"

        return modelo_final, proba_final, {
            "status": estado,
            "brier_raw": float(brier_raw),
            "brier_calibrated": float(brier_cal),
            "auc_raw": float(auc_raw),
            "auc_calibrated": float(auc_cal),
        }
    except Exception as exc:
        print(f"⚠️ Calibracion no aplicada: {exc}")
        return modelo, proba_raw, {
            "status": "calibration_failed",
            "brier_raw": float(brier_raw),
            "auc_raw": float(auc_raw),
        }

scoring_model, y_proba_campeon_val, CALIBRATION_METRICS = calibrar_probabilidades(
    best_model, X_val_proc, y_val, metodo="sigmoid"
)
CALIBRATION_STATUS = CALIBRATION_METRICS["status"]

print("\n📐 CALIBRACIÓN:")
for k, v in CALIBRATION_METRICS.items():
    print(f"   {k}: {v}")

try:
    prob_true, prob_pred = calibration_curve(y_val, y_proba_campeon_val, n_bins=10, strategy="quantile")
    plt.figure(figsize=(6, 5))
    plt.plot(prob_pred, prob_true, marker="o", color=PALETTE_BANCO["accent"], label="Modelo")
    plt.plot([0, 1], [0, 1], linestyle="--", color=PALETTE_BANCO["grid"], label="Calibracion perfecta")
    plt.xlabel("Probabilidad predicha")
    plt.ylabel("Tasa real de default")
    plt.title("Curva de Calibracion - Probabilidad de Default")
    plt.legend()
    plt.tight_layout()
    plt.savefig(PROJECT_ROOT / "reports" / "figures" / "calibration_curve.png", dpi=180)
    plt.close()
except Exception as exc:
    print(f"⚠️ No se pudo graficar calibracion: {exc}")
```

---

### FASE 8: Optimización del Umbral de Decision (Threshold & ROI)

> [!IMPORTANT]
> **REGLA DE NEGOCIO:** El umbral por defecto (0.50) casi nunca maximiza el ROI financiero. Debemos calcular el beneficio neto real variando el threshold.

Definimos los parámetros financieros bajo **las condiciones reales del caso de FinanCrece S.A.**:

```python
# === PARÁMETROS FINANCIEROS DE FINANCRECE S.A. ===
BENEFICIO_PAGADOR_APROBADO = 450   # (TN) Intereses netos cobrados por préstamo sano
COSTO_RECHAZO_OPORTUNIDAD = -150  # (FP) Costo de adquisición / margen perdido por rechazo erróneo
COSTO_DEFAULT_APROBADO = -3000     # (FN) Capital promedio de pérdida por impago/default
BENEFICIO_RECHAZO_EVITADO = 0      # (VP) Evitamos la pérdida, impacto neto neutro

def optimizar_threshold_por_roi(y_true, y_proba):
    thresholds = np.linspace(0.01, 0.99, 99)
    resultados_roi = []
    
    # Caso base (aprobar a todos): tn = 0, fp = 0, así que aprobamos a los pagadores reales (tn) y morosos (fn)
    total_negativos = (y_true == 0).sum()
    total_positivos = (y_true == 1).sum()
    beneficio_base = (total_negativos * BENEFICIO_PAGADOR_APROBADO) + (total_positivos * COSTO_DEFAULT_APROBADO)
    
    for t in thresholds:
        y_pred = (y_proba >= t).astype(int)
        
        # Calcular Matriz de Confusión
        tp = ((y_pred == 1) & (y_true == 1)).sum()
        fp = ((y_pred == 1) & (y_true == 0)).sum()
        fn = ((y_pred == 0) & (y_true == 1)).sum()
        tn = ((y_pred == 0) & (y_true == 0)).sum()
        
        # Métricas tradicionales
        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        
        # ROI Financiero Neto del modelo
        # TN aporta +450, FP cuesta -150 (lost margin), FN cuesta -3000 (capital perdido)
        beneficio_neto_usd = (tn * BENEFICIO_PAGADOR_APROBADO) + (fp * COSTO_RECHAZO_OPORTUNIDAD) + (fn * COSTO_DEFAULT_APROBADO)
        ahorro_neto = beneficio_neto_usd - beneficio_base
        
        resultados_roi.append({
            "threshold": round(t, 2),
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "beneficio_neto_usd": round(beneficio_neto_usd, 2),
            "ahorro_neto_usd": round(ahorro_neto, 2),
            "beneficio_base_usd": round(beneficio_base, 2),
            "roi_ratio": round(beneficio_neto_usd / max(abs(beneficio_base), 1), 2)
        })
        
    df_roi = pd.DataFrame(resultados_roi)
    df_roi.to_csv(PROJECT_ROOT / "reports" / "threshold_analysis.csv", index=False)
    return df_roi

# Calcular ROI para el modelo campeon final; si la calibracion fue aceptada, usar sus probabilidades.
scoring_model = globals().get("scoring_model", best_model)
if "y_proba_campeon_val" not in globals():
    y_proba_campeon_val = scoring_model.predict_proba(X_val_proc)[:, 1]
df_roi = optimizar_threshold_por_roi(y_val, y_proba_campeon_val)

# Encontrar umbrales óptimos
t_optimo_f1 = df_roi.loc[df_roi["f1_score"].idxmax()]
t_optimo_roi = df_roi.loc[df_roi["ahorro_neto_usd"].idxmax()]

print("\n🎯 OPTIMIZACIÓN DE UMBRAL:")
print(f"   ▶️ Umbral óptimo F1-Score: {t_optimo_f1['threshold']} (F1: {t_optimo_f1['f1_score']:.4f}, Recall: {t_optimo_f1['recall']:.4f})")
print(f"   ▶️ Umbral óptimo ROI ($):  {t_optimo_roi['threshold']} (Ahorro Neto vs. Base: USD {t_optimo_roi['ahorro_neto_usd']:.2f})")
```

```python
# === IMPLEMENTACIÓN Y OPTIMIZACIÓN DE LA POLÍTICA DE 3 BANDAS DE RIESGO ===
FACTOR_EXPOSICION_MEDIA = 0.50  # [SUPUESTO] banda media recibe 50% de linea/exposicion

def aplicar_politica_3_bandas(y_true, y_proba, u1=0.10, u2=0.30, verbose=True):
    """
    Bajo Riesgo: aprobar línea completa.
    Riesgo Medio: aprobar condicionado con menor línea, aval o revisión manual.
    Alto Riesgo: rechazar preventivamente.
    """
    df_pol = pd.DataFrame({"real": y_true, "score": y_proba})
    
    def asignar_banda(s):
        if s < u1:
            return "1. Bajo Riesgo (Aprobar)"
        elif s < u2:
            return "2. Riesgo Medio (Condicionar)"
        else:
            return "3. Alto Riesgo (Rechazar)"
            
    df_pol["banda"] = df_pol["score"].apply(asignar_banda)
    
    reporte = df_pol.groupby("banda").agg(
        n_clientes=("score", "count"),
        pct_clientes=("score", lambda x: len(x) / len(df_pol) * 100),
        tasa_mora_real=("real", "mean"),
        score_promedio=("score", "mean")
    ).reset_index()

    def beneficio_banda(row):
        banda = row["banda"]
        real = row["real"]
        if banda.startswith("1."):
            return BENEFICIO_PAGADOR_APROBADO if real == 0 else COSTO_DEFAULT_APROBADO
        if banda.startswith("2."):
            return (
                BENEFICIO_PAGADOR_APROBADO * FACTOR_EXPOSICION_MEDIA
                if real == 0 else COSTO_DEFAULT_APROBADO * FACTOR_EXPOSICION_MEDIA
            )
        return COSTO_RECHAZO_OPORTUNIDAD if real == 0 else BENEFICIO_RECHAZO_EVITADO

    df_pol["beneficio_usd"] = df_pol.apply(beneficio_banda, axis=1)
    beneficio_total = float(df_pol["beneficio_usd"].sum())
    reporte["beneficio_politica_usd"] = beneficio_total
    
    if verbose:
        print("\n📋 REPORTE DE POLÍTICA CREDITICIA DE 3 BANDAS:")
        for _, row in reporte.iterrows():
            print(f"  {row['banda']}: {row['n_clientes']:,} clientes ({row['pct_clientes']:.1f}%) | Mora Real: {row['tasa_mora_real']*100:.2f}% | Score Promedio: {row['score_promedio']:.4f}")
        
    if verbose:
        print(f"  Beneficio estimado politica: USD {beneficio_total:,.2f}")
    return df_pol, reporte, beneficio_total

def optimizar_politica_3_bandas(y_true, y_proba):
    candidatos = []
    grid_bajo = np.linspace(0.03, 0.25, 12)
    grid_alto = np.linspace(0.12, 0.70, 20)

    for u1 in grid_bajo:
        for u2 in grid_alto:
            if u2 <= u1:
                continue
            _, reporte_tmp, beneficio = aplicar_politica_3_bandas(y_true, y_proba, u1=u1, u2=u2, verbose=False)
            candidatos.append({
                "u_bajo": round(float(u1), 3),
                "u_alto": round(float(u2), 3),
                "beneficio_politica_usd": round(float(beneficio), 2),
                "clientes_bajo": int(reporte_tmp.loc[reporte_tmp["banda"].str.startswith("1."), "n_clientes"].sum()),
                "clientes_medio": int(reporte_tmp.loc[reporte_tmp["banda"].str.startswith("2."), "n_clientes"].sum()),
                "clientes_alto": int(reporte_tmp.loc[reporte_tmp["banda"].str.startswith("3."), "n_clientes"].sum()),
            })

    df_politicas = pd.DataFrame(candidatos).sort_values("beneficio_politica_usd", ascending=False)
    df_politicas.to_csv(PROJECT_ROOT / "reports" / "politica_3_bandas_grid.csv", index=False)
    return df_politicas.iloc[0]

# Aplicar política con umbrales optimizados para ROI
politica_optima = optimizar_politica_3_bandas(y_val, y_proba_campeon_val)
df_pol, reporte_bandas, beneficio_bandas = aplicar_politica_3_bandas(
    y_val,
    y_proba_campeon_val,
    u1=politica_optima["u_bajo"],
    u2=politica_optima["u_alto"],
)
reporte_bandas.to_csv(PROJECT_ROOT / "reports" / "politica_3_bandas.csv", index=False)
```

```python
# --- GRÁFICO DE ANÁLISIS DE UMBRAL (DARK MODE) ---
def graficar_roi_vs_f1(df_roi, t_f1, t_roi):
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    # Línea de F1
    color = PALETTE_BANCO["accent"]
    ax1.set_xlabel("Umbral de Decisión")
    ax1.set_ylabel("F1-Score", color=color)
    ax1.plot(df_roi["threshold"], df_roi["f1_score"], color=color, linewidth=2, label="F1-Score")
    ax1.tick_params(axis="y", labelcolor=color)
    ax1.axvline(t_f1, color=color, linestyle="--", alpha=0.7, label=f"F1 Óptimo ({t_f1})")
    
    # Beneficio Neto en eje secundario
    ax2 = ax1.twinx()
    color2 = PALETTE_BANCO["pos"]
    ax2.set_ylabel("Ahorro Neto vs. aprobar todos USD ($)", color=color2)
    ax2.plot(df_roi["threshold"], df_roi["ahorro_neto_usd"], color=color2, linewidth=2.5, label="Ahorro Neto")
    ax2.tick_params(axis="y", labelcolor=color2)
    ax2.axvline(t_roi, color=color2, linestyle="-.", alpha=0.7, label=f"ROI Óptimo ({t_roi})")
    
    plt.title("Optimización de Umbral de Decisión: F1-Score vs ROI Financiero", color="white")
    fig.tight_layout()
    plt.savefig(PROJECT_ROOT / "reports" / "figures" / "threshold_optimization_roi.png", dpi=150)
    plt.close()

graficar_roi_vs_f1(df_roi, t_optimo_f1["threshold"], t_optimo_roi["threshold"])
```

---

### FASE 9: Interpretabilidad del Modelo (Global y Local con SHAP)

> [!TIP]
> **GANAR PUNTOS CON EL JURADO:** No muestres solo un gráfico de importancia de variables nativo del modelo. Utiliza SHAP, ya que cuantifica la dirección y magnitud del efecto de cada variable.

El ejemplo usa `TreeExplainer` porque los candidatos principales son tree-based. Si el campeon final no es compatible con ese explainer, exportar una importancia alternativa reproducible y documentar la razon.

```python
try:
    import shap
except ImportError:
    print("⚠️ SHAP no está instalado. Ejecute 'pip install shap' para habilitar esta fase.")
    shap = None

def ejecutar_interpretabilidad_shap(modelo, X_t_p, X_v_p, feature_names):
    if not shap: return
    
    # Convertir a DataFrame para nombres legibles
    X_val_df = pd.DataFrame(X_v_p, columns=feature_names)
    
    # Usar TreeExplainer de SHAP
    explainer = shap.TreeExplainer(modelo)
    shap_values = explainer(X_val_df)
    
    # 1. Gráfico Resumen SHAP (Beeswarm)
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X_val_df, show=False)
    plt.title("Impacto SHAP de Variables en Default 90d", fontsize=14, color="white")
    plt.tight_layout()
    plt.savefig(PROJECT_ROOT / "reports" / "figures" / "shap_summary.png", dpi=200, facecolor="#0A1628")
    plt.close()
    
    # 2. Guardar Importancia SHAP media a CSV
    shap_importance = np.abs(shap_values.values).mean(axis=0)
    df_imp = pd.DataFrame({
        "Feature": feature_names,
        "SHAP Importance": shap_importance
    }).sort_values("SHAP Importance", ascending=False)
    
    df_imp.to_csv(PROJECT_ROOT / "reports" / "feature_importance.csv", index=False)
    print("✅ Interpretabilidad SHAP exportada exitosamente.")

# Ejecutar interpretacion del campeon
ejecutar_interpretabilidad_shap(best_model, X_train_proc, X_val_proc, feature_names_out)
```

---

### FASE 10: Análisis Detallado de Errores

Guardamos las predicciones del modelo campeón en el set de validación para entender a fondo las causas de los **Falsos Negativos** (clientes que entraron en default pero fueron aprobados) y **Falsos Positivos** (buenos clientes que serían rechazados).

```python
def ejecutar_analisis_errores(modelo, X_val_raw, X_val_p, y_true, t_decision):
    """Guarda predicciones y genera tabla de perfiles de error."""
    y_proba = modelo.predict_proba(X_val_p)[:, 1]
    y_pred = (y_proba >= t_decision).astype(int)
    
    df_err = X_val_raw.copy()
    df_err["real"] = y_true.values
    df_err["score"] = y_proba
    df_err["pred"] = y_pred
    
    # Categorizar tipos de predicciones
    condiciones = [
        (df_err["real"] == 1) & (df_err["pred"] == 1),
        (df_err["real"] == 0) & (df_err["pred"] == 0),
        (df_err["real"] == 0) & (df_err["pred"] == 1),
        (df_err["real"] == 1) & (df_err["pred"] == 0)
    ]
    opciones = ["Verdadero Positivo (TP)", "Verdadero Negativo (TN)", "Falso Positivo (FP)", "Falso Negativo (FN)"]
    df_err["resultado"] = np.select(condiciones, opciones, default="Desconocido")
    
    # Exportar predicciones para revisión posterior
    df_err.to_csv(PROJECT_ROOT / "reports" / "predicciones_validacion.csv", index=False)
    
    # Generar tabla resumen de medias por tipo de resultado
    resumen_errores = df_err.groupby("resultado").mean(numeric_only=True)
    resumen_errores.to_csv(PROJECT_ROOT / "reports" / "profile_error_analysis.csv")
    
    print("✅ Análisis de errores finalizado y exportado.")
    return df_err

# Ejecutar con el umbral optimo de ROI
df_errores = ejecutar_analisis_errores(scoring_model, X_val, X_val_proc, y_val, t_optimo_roi["threshold"])
```

---

### FASE 11: Seleccion Final y Serializacion del Modelo

Se serializa el campeon real y luego se verifica el gate completo. Asi `entregables_exportados` no bloquea circularmente la misma exportacion que debe comprobar.

```python
import joblib

# Actualizar gates tecnicos del campeon real
GATE_CONDITIONS["modelos_minimos_entrenados"] = len(resultados) >= 4
GATE_CONDITIONS["overfitting_bajo"]         = best_result["Overfitting Gap"] < 0.05
GATE_CONDITIONS["metricas_credito_ok"]      = (
    best_result["ROC-AUC Val"] >= 0.75
    and best_result["KS Val"] >= 0.30
    and best_result["Gini Val"] >= 0.50
)
GATE_CONDITIONS["calibracion_revisada"]     = "CALIBRATION_STATUS" in globals()
GATE_CONDITIONS["threshold_optimizado"]     = (
    "ahorro_neto_usd" in df_roi.columns
    and (PROJECT_ROOT / "reports" / "politica_3_bandas.csv").exists()
)
GATE_CONDITIONS["interpretabilidad_exportada"] = (
    (PROJECT_ROOT / "reports" / "figures" / "shap_summary.png").exists()
    or (PROJECT_ROOT / "reports" / "feature_importance.csv").exists()
)

# Guardar preprocesador y campeon
(PROJECT_ROOT / "models").mkdir(parents=True, exist_ok=True)
joblib.dump(preprocessor, PROJECT_ROOT / "models" / "preprocessor.joblib")
final_model = globals().get("scoring_model", best_model)
joblib.dump(final_model, PROJECT_ROOT / "models" / "best_model.joblib")

# Guardar metadatos finales en JSON
metadata = {
    "target_col": TARGET_COL,
    "model_name": best_name,
    "calibration_status": globals().get("CALIBRATION_STATUS", "not_reviewed"),
    "calibration_metrics": globals().get("CALIBRATION_METRICS", {}),
    "optimal_threshold": float(t_optimo_roi["threshold"]),
    "policy_3_bands": {
        "u_bajo": float(politica_optima["u_bajo"]),
        "u_alto": float(politica_optima["u_alto"]),
        "factor_exposicion_media": FACTOR_EXPOSICION_MEDIA,
    },
    "validation_metrics": {
        "roc_auc": float(best_result["ROC-AUC Val"]),
        "pr_auc": float(best_result["PR-AUC Val"]),
        "f1_score": float(best_result["F1-Score Val"]),
        "ks": float(best_result["KS Val"]),
        "gini": float(best_result["Gini Val"]),
        "lift_top10": float(best_result["Lift@10% Val"])
    },
    "model_input_columns": X_train.columns.tolist(),
    "features_order": feature_names_out,
    "feature_builder_path": FEATURE_BUILDER_PATH,
}

with open(PROJECT_ROOT / "models" / "model_metadata.json", "w") as f:
    json.dump(metadata, f, indent=4)

GATE_CONDITIONS["entregables_exportados"] = all([
    (PROJECT_ROOT / "models" / "preprocessor.joblib").exists(),
    (PROJECT_ROOT / "models" / "best_model.joblib").exists(),
    (PROJECT_ROOT / "models" / "model_metadata.json").exists(),
])
gate_aprobado = verificar_gate_modelo()
if not gate_aprobado:
    print("⚠️ ALERTA: Se exporto el mejor intento, pero faltan gates; activar feedback loop.")

print("💾 Todos los entregables técnicos han sido serializados en models/")
```

---

### FASE 12: Generacion del Archivo de Submission Final

Si el datathon provee un dataset de prueba sin target (`data/raw/TEST.sav` o similar), primero se aplica el mismo feature builder del EDA y despues el preprocessor entrenado. El formato final de columnas debe respetar `submission_spec` extraido por el Orquestador.

```python
def generar_submission(test_raw_path, output_sub_path):
    """Aplica feature builder + preprocessor + campeon sobre test raw."""
    print("🚀 Iniciando generación de predicciones de prueba...")
    
    # 1. Cargar artefactos guardados
    preproc = joblib.load(PROJECT_ROOT / "models" / "preprocessor.joblib")
    modelo = joblib.load(PROJECT_ROOT / "models" / "best_model.joblib")
    with open(PROJECT_ROOT / "models" / "model_metadata.json", "r") as f:
        meta_saved = json.load(f)
        
    t_opt = meta_saved["optimal_threshold"]
    if not meta_saved.get("feature_builder_path"):
        raise ValueError("Submission desde test raw requiere src/feature_builder.py en el handoff.")
    from src.feature_builder import build_features
    
    # 2. Cargar datos de test raw
    # Soporte para pyreadstat u otros
    ext = Path(test_raw_path).suffix.lower()
    if ext == ".sav":
        import pyreadstat
        df_t, _ = pyreadstat.read_sav(test_raw_path)
    elif ext == ".xlsx":
        df_t = pd.read_excel(test_raw_path)
    else:
        df_t = pd.read_csv(test_raw_path)
        
    # Verificar columnas id
    id_col_present = [c for c in ID_COLS if c in df_t.columns][0]
    
    # 3. Repetir ingenieria de features y alinear columnas de entrada
    df_t_features = build_features(df_t.copy())
    missing_model_cols = sorted(
        set(meta_saved["model_input_columns"]) - set(df_t_features.columns)
    )
    if missing_model_cols:
        raise ValueError(f"Test sin features esperadas por el modelo: {missing_model_cols[:10]}")

    X_t = df_t_features.reindex(columns=meta_saved["model_input_columns"])
    X_t_proc = preproc.transform(X_t)
    
    # 4. Predecir score y clase usando el threshold óptimo
    scores = modelo.predict_proba(X_t_proc)[:, 1]
    classes = (scores >= t_opt).astype(int)
    
    # 5. Guardar entregable final
    df_sub = pd.DataFrame({
        id_col_present: df_t[id_col_present],
        "score": scores,
        "pred": classes
    })
    
    df_sub.to_csv(output_sub_path, index=False)
    print(f"💾 Submission guardada exitosamente en {output_sub_path} | Registros: {df_sub.shape[0]:,}")
    return df_sub
```

---

## 3. UMBRALES DE EXCELENCIA Y PROTOCOLO DE FEEDBACK

Alineado con el **Orquestador**, el proceso de modelado requiere una autoevaluación constante para forzar la mejora de la solución predictiva.

### 3.1 Criterios de Evaluación

| Métrica | Insuficiente | Aceptable | Excelente | Sospechoso / Leakage |
|---|---|---|---|---|
| **ROC-AUC** | < 0.70 | 0.70 – 0.80 | 0.85 – 0.95 | > 0.95 |
| **Overfitting Gap** | > 0.08 | 0.05 – 0.08 | < 0.03 | — |
| **Lift Top 10%** | < 2.0x | 2.0 – 3.0x | 4.0 – 5.5x | > 6.0x |

---

### 3.2 Protocolo de Feedback Loop a EDA (Doc 1)

Si las métricas del modelo caen en **"Insuficiente"** o **"Aceptable"**, el modelo **NO** es apto para presentarse ante el jurado. Se debe activar el protocolo de retroalimentación para volver a la etapa de ingeniería de variables (`EDA_Guia_Datathon_Banca.md`).

```
                                  Métricas Insuficientes
                                           │
         ┌─────────────────────────────────┴─────────────────────────────────┐
         ▼                                 ▼                                 ▼
¿Top 10 variables son Raw?       Overfitting Gap > 0.08             Falsos Negativos muy altos
         │                                 │                                 │
         ▼                                 ▼                                 ▼
[Acción]: Volver a EDA.         [Acción]: Volver a EDA.           [Acción]: Volver a EDA.
Crear interacciones, ratios y    Remover variables inestables y    Crear variables de perfil
variables de tendencia.          aplicar regularización extrema.   transaccional reciente (recency).
```

#### Código de comunicación de feedback:
El modelo escribe un archivo temporal de feedback para que la siguiente iteración del EDA sepa exactamente qué ajustar:

```python
import json

def activar_feedback_loop_eda(motivo, sugerencias_features, vars_a_remover=[]):
    """Genera archivo de handoff para que el EDA se re-ejecute enfocado en resolver debilidades."""
    feedback = {
        "estado": "requiere_iteracion",
        "motivo": motivo,
        "auc_actual": float(best_result["ROC-AUC Val"]),
        "sugerencias_features": sugerencias_features,
        "vars_a_remover": vars_a_remover,
        "fecha_solicitud": pd.Timestamp.now().isoformat()
    }
    
    with open(PROJECT_ROOT / "reports" / "modelo_feedback_a_eda.json", "w") as f:
        json.dump(feedback, f, indent=4)
        
    print("🚨 feedback_loop ACTIVADO. Se requiere regresar al EDA (Doc 1).")
```

---

## 4. CÓDIGO DE COPILOTO: PLANTILLA JUPYTER MINIMA

Para crear un notebook de entrega profesional (`notebooks/ENTREGA_DATATHON.ipynb`), usar el siguiente bloque como arranque minimo. Antes de presentarlo se debe integrar el handoff real, el feature builder si aplica, los artefactos del flujo completo y verificar `Restart & Run All` con los datos del caso.

```python
# ==============================================================================
# 🏦 PIPELINE DE MODELADO, VALIDACIÓN Y EVALUACIÓN DE EXCELENCIA BANCARIA
# ==============================================================================
# random_state = 42 | Dark Mode Corporativo | No Fuga de Información
# ==============================================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import json
import warnings
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler
from sklearn.impute import SimpleImputer
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import (
    roc_auc_score, precision_recall_curve, auc, f1_score,
    recall_score, precision_score, log_loss, brier_score_loss, confusion_matrix
)

warnings.filterwarnings("ignore")

try:
    import lightgbm as lgb
except ImportError:
    lgb = None

try:
    from catboost import CatBoostClassifier
except ImportError:
    CatBoostClassifier = None

# --- 1. CONFIGURACIÓN ---
PROJECT_ROOT = Path(".")
TARGET_COL = "default_90d"
ID_COLS = ["id_cliente"]
RANDOM_STATE = 42

# --- 2. CONFIGURAR ESTILO CORPORATIVO (DARK MODE) ---
plt.style.use("dark_background")
plt.rcParams.update({
    "figure.facecolor": "#0A1628",
    "axes.facecolor": "#0A1628",
    "text.color": "#FFFFFF",
    "axes.labelcolor": "#FFFFFF",
    "xtick.color": "#FFFFFF",
    "ytick.color": "#FFFFFF",
    "grid.color": "#1C2D42"
})

# --- 3. CARGAR DATOS ---
df = pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "features.parquet")
X = df.drop(columns=[TARGET_COL] + ID_COLS, errors="ignore")
y = df[TARGET_COL]

# --- 4. VALIDACIÓN DE DATOS (SPLIT ESTRATIFICADO) ---
X_train_full, X_test, y_train_full, y_test = train_test_split(
    X, y, test_size=0.20, random_state=RANDOM_STATE, stratify=y
)
X_train, X_val, y_train, y_val = train_test_split(
    X_train_full, y_train_full, test_size=0.25, random_state=RANDOM_STATE, stratify=y_train_full
)

# --- 5. PREPROCESAMIENTO ---
num_cols = X_train.select_dtypes(include=["int64", "float64"]).columns.tolist()
cat_cols = X_train.select_dtypes(include=["object", "category", "bool"]).columns.tolist()

num_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", RobustScaler())
])
cat_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="constant", fill_value="Desconocido")),
    ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
])
preprocessor = ColumnTransformer(transformers=[
    ("num", num_transformer, num_cols),
    ("cat", cat_transformer, cat_cols)
])

X_train_proc = preprocessor.fit_transform(X_train)
X_val_proc   = preprocessor.transform(X_val)

# --- 6. ENTRENAR MODELOS ---
pos_weight = (len(y_train) - sum(y_train)) / sum(y_train)

# Baselines
dummy = DummyClassifier(strategy="stratified", random_state=RANDOM_STATE).fit(X_train_proc, y_train)
logreg = LogisticRegression(class_weight="balanced", random_state=RANDOM_STATE, max_iter=1000).fit(X_train_proc, y_train)

# Avanzados con fallback local
rf = RandomForestClassifier(n_estimators=300, max_depth=8, class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1).fit(X_train_proc, y_train)
modelos = [
    (dummy, "Dummy"),
    (logreg, "Logistic Regression"),
    (rf, "Random Forest"),
]

if lgb is not None:
    lgbm = lgb.LGBMClassifier(n_estimators=400, learning_rate=0.03, scale_pos_weight=pos_weight, random_state=RANDOM_STATE, verbosity=-1).fit(X_train_proc, y_train)
    modelos.append((lgbm, "LightGBM"))
else:
    hgb = HistGradientBoostingClassifier(max_iter=250, learning_rate=0.05, random_state=RANDOM_STATE).fit(X_train_proc, y_train)
    modelos.append((hgb, "HistGradientBoosting"))

if CatBoostClassifier is not None:
    cat = CatBoostClassifier(iterations=500, learning_rate=0.04, auto_class_weights="Balanced", random_state=RANDOM_STATE, verbose=False).fit(X_train_proc, y_train)
    modelos.append((cat, "CatBoost"))

# --- 7. EVALUACIÓN Y SELECCIÓN ---
def evaluar(mod, X_t, y_t, X_v, y_v, name):
    prob_t = mod.predict_proba(X_t)[:, 1]
    prob_v = mod.predict_proba(X_v)[:, 1]
    pred_v = (prob_v >= 0.5).astype(int)
    return {
        "Modelo": name,
        "AUC Train": round(roc_auc_score(y_t, prob_t), 4),
        "AUC Val": round(roc_auc_score(y_v, prob_v), 4),
        "F1 Val": round(f1_score(y_v, pred_v), 4),
        "Recall Val": round(recall_score(y_v, pred_v), 4)
    }

resultados_df = pd.DataFrame([
    evaluar(mod, X_train_proc, y_train, X_val_proc, y_val, name)
    for mod, name in modelos
])
print(resultados_df.to_markdown(index=False))
best_name = resultados_df.sort_values("AUC Val", ascending=False).iloc[0]["Modelo"]
best_model = next(mod for mod, name in modelos if name == best_name)

# --- 8. SERIALIZAR CAMPEÓN ---
joblib.dump(preprocessor, PROJECT_ROOT / "models" / "preprocessor.joblib")
joblib.dump(best_model, PROJECT_ROOT / "models" / "best_model.joblib")
print("🎉 ¡Pipeline de excelencia completado exitosamente!")
```
