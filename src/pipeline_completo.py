"""
PIPELINE COMPLETO — Datathon FinanCrece S.A. — ESAN 2026
Auditor Senior de ML / Scoring de Crédito Bancario

CASO REAL DETECTADO:
- Dataset: German Credit adaptado (800 train, 200 test)
- Target: columna 'target' → 'bad'=default, 'good'=pagador
- Tasa de default: 29.5% (desbalance MODERADO)
- Variables: mix categóricas/numéricas del dominio crediticio
- Submission: id_cliente + prob_default (columna Probabilidad del test)

ESTRATEGIA:
1. Mapear target a 0/1 (good=0, bad=1)
2. EDA con variables reales del German Credit
3. Feature engineering crediticio adaptado
4. Modelos con fallback garantizado
5. Métricas completas: AUC, Gini, KS, Brier, Lift@10
6. ROI financiero y política de 3 bandas
7. Submission.csv + notebook limpio
"""

import pandas as pd
import numpy as np
import json
import warnings
import joblib
from pathlib import Path
from datetime import datetime

warnings.filterwarnings("ignore")
pd.set_option("display.max_columns", 200)

# ============================================================
# CONFIGURACIÓN ADAPTADA AL CASO REAL
# ============================================================
PROJECT_ROOT = Path(".")
TARGET_COL = "default_90d"        # nombre canonical del Datathon
TARGET_RAW = "target"              # nombre real en el dataset
TARGET_POSITIVE = "bad"            # valor que representa default
ID_COLS = ["id_cliente"]
ID_ADICIONAL = "id_adicional"
SUBMISSION_COL = "Probabilidad"    # columna del test a llenar
TIPO_PROBLEMA = "clasificacion_binaria"
METRICA_JURADO = "roc_auc"
VALIDATION_STRATEGY = "stratified_split"
RANDOM_STATE = 42

# Matriz económica FinanCrece S.A.
GANANCIA_BUEN_APROBADO = 450
COSTO_BUEN_RECHAZADO = -150
PERDIDA_DEFAULT_APROBADO = -3000
VALOR_DEFAULT_RECHAZADO = 0
FACTOR_EXPOSICION_MEDIA = 0.50  # [SUPUESTO]

# ============================================================
# SETUP VISUAL DARK MODE
# ============================================================
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

PALETTE = {
    "pos": "#F5A623", "neg": "#2D6DB5",
    "bg": "#0A1628", "text": "#FFFFFF",
    "grid": "#1E3A5F", "face": "#0D1F38",
    "accent": "#00E5FF", "neutral": "#A0AEC0",
}

plt.rcParams.update({
    "figure.facecolor": PALETTE["bg"], "axes.facecolor": PALETTE["face"],
    "axes.labelcolor": PALETTE["text"], "xtick.color": PALETTE["text"],
    "ytick.color": PALETTE["text"], "text.color": PALETTE["text"],
    "axes.titlecolor": PALETTE["text"], "axes.spines.top": False,
    "axes.spines.right": False, "axes.edgecolor": PALETTE["grid"],
    "grid.color": PALETTE["grid"], "grid.alpha": 0.4,
    "figure.dpi": 150, "savefig.dpi": 150, "savefig.bbox": "tight",
    "savefig.facecolor": PALETTE["bg"],
})

FIG_DIR = PROJECT_ROOT / "reports" / "figures"
for d in ["data/raw","data/processed","reports","reports/figures","models","src","notebooks"]:
    (PROJECT_ROOT / d).mkdir(parents=True, exist_ok=True)

def save_fig(name):
    plt.savefig(FIG_DIR / f"{name}.png", bbox_inches="tight")
    plt.close()
    print(f"  📊 {name}.png")

# ============================================================
# PASO 1 — CARGA Y PREPARACIÓN DE DATOS
# ============================================================
print("\n" + "="*65)
print("PASO 1 — CARGA Y PREPARACIÓN")
print("="*65)

df_raw = pd.read_excel(PROJECT_ROOT / "dataInicial" / "dataset_credito-train.xlsx", engine="openpyxl")
df_test_raw = pd.read_excel(PROJECT_ROOT / "dataInicial" / "dataset_credito-test.xlsx", engine="openpyxl")

print(f"TRAIN: {df_raw.shape[0]:,} × {df_raw.shape[1]} | TEST: {df_test_raw.shape[0]:,} × {df_test_raw.shape[1]}")

# Mapear target a 0/1
df_raw[TARGET_COL] = (df_raw[TARGET_RAW] == TARGET_POSITIVE).astype(int)
print(f"\nTarget mapeado: '{TARGET_RAW}' → '{TARGET_COL}'")
vc = df_raw[TARGET_COL].value_counts()
tasa_default = df_raw[TARGET_COL].mean()
print(f"Default (1=bad): {vc[1]:,} ({tasa_default*100:.1f}%)")
print(f"Pagador (0=good): {vc[0]:,} ({(1-tasa_default)*100:.1f}%)")
print(f"Desbalance: {vc[0]/vc[1]:.1f}:1 (MODERADO)")

# Identificar columnas
# pandas 3.x: string columns have dtype 'object' or 'str' (StringDtype)
cat_cols_raw = [c for c in df_raw.columns 
                if (df_raw[c].dtype == object or str(df_raw[c].dtype) in ['string','StringDtype','object'])
                and c not in [TARGET_RAW, TARGET_COL, "id_cliente"]]
num_cols_raw = [c for c in df_raw.columns 
                if df_raw[c].dtype in ["int64","float64","int32","float32"] 
                and c not in ["id_cliente", TARGET_COL]]
print(f"\nCatégóricas: {cat_cols_raw}")
print(f"Numéricas: {num_cols_raw}")

# Guardar base original
df_raw.to_parquet(PROJECT_ROOT / "data" / "processed" / "base_original.parquet", index=False)

# ============================================================
# PASO 2 — EDA Y ANÁLISIS DE CALIDAD
# ============================================================
print("\n" + "="*65)
print("PASO 2 — EDA")
print("="*65)

# Nulos
print(f"\nNulos TRAIN:")
nulos = df_raw.isna().sum()
if nulos.sum() == 0:
    print("  ✅ Sin valores nulos en train")
else:
    print(nulos[nulos > 0])

print(f"\nNulos TEST:")
nulos_test = df_test_raw.isna().sum()
nulos_test_real = nulos_test[nulos_test > 0]
nulos_test_real = nulos_test_real[nulos_test_real.index != SUBMISSION_COL]
if len(nulos_test_real) == 0:
    print("  ✅ Sin valores nulos en test (excepto columna Probabilidad a predecir)")
else:
    print(nulos_test_real)

# Duplicados
dup = df_raw.duplicated().sum()
dup_id = df_raw["id_cliente"].duplicated().sum()
print(f"\nDuplicados exactos: {dup} | Duplicados id_cliente: {dup_id}")

# Default rate por variable categórica
print("\n--- Default Rate por Variable Categórica ---")
biv_cat = []
for col in cat_cols_raw:
    dr = df_raw.groupby(col)[TARGET_COL].agg(["mean","count"])
    dr.columns = ["default_rate","n"]
    dr["variable"] = col
    dr = dr.reset_index()
    biv_cat.append(dr)
    top_risk = dr.sort_values("default_rate", ascending=False).iloc[0]
    bot_risk = dr.sort_values("default_rate", ascending=False).iloc[-1]
    print(f"  {col}: max_dr={top_risk['default_rate']:.3f}({top_risk[col]}), min_dr={bot_risk['default_rate']:.3f}({bot_risk[col]})")

# Default rate por numérica (cuartiles)
print("\n--- Default Rate por Cuartil de Variables Numéricas ---")
for col in num_cols_raw:
    try:
        q = pd.qcut(df_raw[col], q=4, duplicates="drop")
        dr = df_raw.groupby(q, observed=True)[TARGET_COL].mean().round(3)
        print(f"  {col}: {dr.values.tolist()}")
    except Exception:
        pass

# Correlación con target
print("\n--- Correlación con Target ---")
corr_target = df_raw[num_cols_raw + [TARGET_COL]].corr()[TARGET_COL].drop(TARGET_COL)
corr_target = corr_target.reindex(corr_target.abs().sort_values(ascending=False).index)
print(corr_target.round(4).to_string())

# Gráfico: Distribución del target
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
ax1.bar(["Pagador (good)", "Default (bad)"], [vc[0], vc[1]], color=[PALETTE["neg"], PALETTE["pos"]], edgecolor="white")
for i, (label, val) in enumerate(zip(["Pagador", "Default"], [vc[0], vc[1]])):
    ax1.text(i, val + 5, f"{val:,}\n({val/len(df_raw)*100:.1f}%)", ha="center", fontsize=12, fontweight="bold")
ax1.set_title("Distribución del Target", fontsize=14, fontweight="bold")
ax1.set_ylabel("N° Clientes")

# Barras de default rate por checking_status
dr_check = df_raw.groupby("checking_status")[TARGET_COL].mean().sort_values(ascending=False)
colors_bar = [PALETTE["pos"] if v > tasa_default else PALETTE["neg"] for v in dr_check.values]
ax2.bar(range(len(dr_check)), dr_check.values, color=colors_bar, edgecolor="white")
ax2.axhline(y=tasa_default, color=PALETTE["accent"], linestyle="--", linewidth=2, label=f"Promedio: {tasa_default:.2%}")
ax2.set_xticks(range(len(dr_check)))
ax2.set_xticklabels([s[:15] for s in dr_check.index], rotation=30, ha="right", fontsize=8)
ax2.set_title("Default Rate por Checking Status", fontsize=13, fontweight="bold")
ax2.set_ylabel("Tasa de Default")
ax2.legend()
plt.suptitle("FinanCrece S.A. — EDA Principal", fontsize=14, fontweight="bold", y=1.01)
plt.tight_layout()
save_fig("eda_target_y_checking")

# Gráfico: Variables numéricas por default
fig, axes = plt.subplots(2, 4, figsize=(18, 9))
axes = axes.flatten()
for i, col in enumerate(num_cols_raw[:7]):
    ax = axes[i]
    for val, color, label in [(0, PALETTE["neg"], "Pagador"), (1, PALETTE["pos"], "Default")]:
        data = df_raw[df_raw[TARGET_COL] == val][col].dropna()
        ax.hist(data, bins=30, color=color, alpha=0.7, label=label, density=True, edgecolor="none")
    ax.set_title(f"{col}", fontsize=10, fontweight="bold")
    ax.legend(fontsize=7)
for j in range(len(num_cols_raw), 8):
    axes[j].set_visible(False)
plt.suptitle("FinanCrece — Distribución de Variables Numéricas por Default", fontsize=13, fontweight="bold")
plt.tight_layout()
save_fig("num_vars_by_target")

# ============================================================
# PASO 3 — FEATURE ENGINEERING ADAPTADO AL GERMAN CREDIT
# ============================================================
print("\n" + "="*65)
print("PASO 3 — FEATURE ENGINEERING")
print("="*65)

def build_features_german(df_input: pd.DataFrame) -> pd.DataFrame:
    """
    Feature engineering adaptado al German Credit Dataset.
    Solo transformaciones fila a fila — sin fit de parámetros.
    Reproducible para train y test.
    """
    fe = pd.DataFrame(index=df_input.index)

    # --- 1. DURACIÓN DEL CRÉDITO ---
    if "duration" in df_input.columns:
        fe["duration_largo"] = (df_input["duration"] > 24).astype(int)
        fe["duration_corto"] = (df_input["duration"] <= 12).astype(int)
        fe["log_duration"] = np.log1p(df_input["duration"])

    # --- 2. MONTO DEL CRÉDITO ---
    if "credit_amount" in df_input.columns:
        fe["log_credit_amount"] = np.log1p(df_input["credit_amount"])
        fe["monto_alto"] = (df_input["credit_amount"] > 5000).astype(int)
        fe["monto_bajo"] = (df_input["credit_amount"] < 1000).astype(int)

    # --- 3. CARGA FINANCIERA: Monto × Duración ---
    if "duration" in df_input.columns and "credit_amount" in df_input.columns:
        fe["carga_financiera"] = df_input["credit_amount"] * df_input["duration"]
        fe["log_carga"] = np.log1p(fe["carga_financiera"])
        fe["cuota_estimada"] = df_input["credit_amount"] / df_input["duration"].clip(lower=1)
        fe["log_cuota"] = np.log1p(fe["cuota_estimada"])

    # --- 4. CHECKING STATUS (estado de cuenta corriente — MUY PREDICTIVO) ---
    # Ordinal encoding basado en riesgo bancario conocido
    checking_risk = {"<0": 3, "0<=X<200": 2, ">=200": 1, "no checking": 0}
    if "checking_status" in df_input.columns:
        fe["checking_risk_ordinal"] = df_input["checking_status"].map(checking_risk).fillna(2)
        fe["sin_cuenta_corriente"] = (df_input["checking_status"] == "no checking").astype(int)
        fe["cuenta_negativa"] = (df_input["checking_status"] == "<0").astype(int)
        fe["cuenta_baja"] = (df_input["checking_status"] == "0<=X<200").astype(int)
        fe["cuenta_buena"] = (df_input["checking_status"] == ">=200").astype(int)

    # --- 5. HISTORIAL CREDITICIO (ordinal por riesgo) ---
    history_risk = {
        "no credits/all paid": 4,   # nunca ha necesitado — riesgo por falta de historial
        "all paid": 3,
        "existing paid": 2,
        "delayed previously": 2,    # pagó pero con retrasos
        "critical/other existing credit": 1,  # menor riesgo: ya experimentado y solvente
    }
    if "credit_history" in df_input.columns:
        fe["history_risk_ordinal"] = df_input["credit_history"].map(history_risk).fillna(2)
        fe["historial_limpio"] = (df_input["credit_history"] == "existing paid").astype(int)
        fe["historial_critico"] = (df_input["credit_history"].isin(["no credits/all paid","all paid"])).astype(int)
        fe["historial_delay"] = (df_input["credit_history"] == "delayed previously").astype(int)

    # --- 6. SAVINGS STATUS (ahorros disponibles) ---
    savings_risk = {"<100": 4, "100<=X<500": 3, "500<=X<1000": 2, ">=1000": 1, "no known savings": 0}
    if "savings_status" in df_input.columns:
        fe["savings_risk_ordinal"] = df_input["savings_status"].map(savings_risk).fillna(2)
        fe["sin_ahorros"] = (df_input["savings_status"] == "<100").astype(int)
        fe["ahorros_altos"] = (df_input["savings_status"].isin([">=1000","no known savings"])).astype(int)

    # --- 7. EMPLEO (estabilidad laboral) ---
    employment_risk = {"unemployed": 4, "<1": 3, "1<=X<4": 2, "4<=X<7": 1, ">=7": 0}
    if "employment" in df_input.columns:
        fe["employment_risk_ordinal"] = df_input["employment"].map(employment_risk).fillna(2)
        fe["desempleado"] = (df_input["employment"] == "unemployed").astype(int)
        fe["empleo_estable"] = (df_input["employment"] == ">=7").astype(int)

    # --- 8. EDAD ---
    if "age" in df_input.columns:
        fe["edad_limpia"] = df_input["age"].clip(lower=18, upper=80)
        fe["joven"] = (df_input["age"] < 30).astype(int)
        fe["maduro"] = (df_input["age"] >= 45).astype(int)
        fe["log_age"] = np.log1p(df_input["age"])

    # --- 9. COMPROMISO DE CUOTA (installment commitment) ---
    if "installment_commitment" in df_input.columns:
        fe["cuota_alta_pct"] = (df_input["installment_commitment"] >= 4).astype(int)
        fe["cuota_baja_pct"] = (df_input["installment_commitment"] <= 2).astype(int)

    # --- 10. INTERACCIONES CREDITICIAS CLAVE ---
    # Riesgo cuenta × historial
    if "checking_risk_ordinal" in fe.columns and "history_risk_ordinal" in fe.columns:
        fe["riesgo_combinado"] = fe["checking_risk_ordinal"] * fe["history_risk_ordinal"]

    # Cuenta negativa + monto alto = mayor riesgo
    if "cuenta_negativa" in fe.columns and "monto_alto" in fe.columns:
        fe["negativo_y_monto_alto"] = (fe["cuenta_negativa"] & fe["monto_alto"]).astype(int)

    # Joven sin historial con monto alto
    if "joven" in fe.columns and "historial_limpio" in fe.columns and "monto_alto" in fe.columns:
        fe["joven_riesgo_alto"] = (fe["joven"] & ~fe["historial_limpio"].astype(bool) & fe["monto_alto"]).astype(int)

    # Sin ahorros + cuenta negativa
    if "sin_ahorros" in fe.columns and "cuenta_negativa" in fe.columns:
        fe["sin_reservas"] = (fe["sin_ahorros"] & fe["cuenta_negativa"]).astype(int)

    # Carga financiera / riesgo cuenta
    if "carga_financiera" in fe.columns and "checking_risk_ordinal" in fe.columns:
        safe_check = (4 - fe["checking_risk_ordinal"]).clip(lower=0.1)
        fe["carga_vs_cuenta"] = fe["log_carga"] / safe_check

    # --- 11. PROPÓSITO DEL CRÉDITO (riesgo por destino) ---
    purpose_risk_high = ["new car", "furniture/equipment", "radio/tv"]
    purpose_risk_low = ["business", "education", "repairs"]
    if "purpose" in df_input.columns:
        fe["proposito_consumo"] = df_input["purpose"].isin(purpose_risk_high).astype(int)
        fe["proposito_productivo"] = df_input["purpose"].isin(purpose_risk_low).astype(int)

    # --- 12. GÉNERO/ESTADO CIVIL (codificación ordinal informativa) ---
    if "personal_status" in df_input.columns:
        fe["es_mujer"] = df_input["personal_status"].str.contains("female", case=False, na=False).astype(int)
        fe["divorciado_hombre"] = (df_input["personal_status"] == "male div/sep").astype(int)

    # --- 13. HOUSING ---
    housing_risk = {"rent": 2, "for free": 1, "own": 0}
    if "housing" in df_input.columns:
        fe["housing_risk"] = df_input["housing"].map(housing_risk).fillna(1)

    # --- 14. SCORE DE RIESGO COMPUESTO (fila a fila) ---
    componentes = []
    if "checking_risk_ordinal" in fe.columns:
        componentes.append(30 * fe["checking_risk_ordinal"])
    if "history_risk_ordinal" in fe.columns:
        componentes.append(20 * fe["history_risk_ordinal"])
    if "savings_risk_ordinal" in fe.columns:
        componentes.append(15 * fe["savings_risk_ordinal"])
    if "employment_risk_ordinal" in fe.columns:
        componentes.append(10 * fe["employment_risk_ordinal"])
    if "log_carga" in fe.columns:
        componentes.append(5 * fe["log_carga"])
    if componentes:
        fe["score_riesgo_compuesto"] = sum(componentes)

    return fe


# Aplicar feature engineering
fe_train = build_features_german(df_raw)
fe_test = build_features_german(df_test_raw)

print(f"Features nuevas creadas: {len(fe_train.columns)}")
print(f"Features nuevas: {list(fe_train.columns)}")

# Consolidar train
drop_from_raw = ["target", TARGET_COL]  # ya mapeado
raw_keep = [c for c in df_raw.columns if c not in drop_from_raw]
new_fe_cols = [c for c in fe_train.columns if c not in df_raw.columns]

df_fe = pd.concat([
    df_raw[raw_keep + [TARGET_COL]],
    fe_train[new_fe_cols]
], axis=1)

# Consolidar test
raw_keep_test = [c for c in df_test_raw.columns if c != SUBMISSION_COL]
df_fe_test = pd.concat([
    df_test_raw[raw_keep_test],
    fe_test[new_fe_cols]
], axis=1)

# Eliminar constantes
const_cols = [c for c in df_fe.columns if df_fe[c].nunique() <= 1 and c not in ["id_cliente", TARGET_COL]]
if const_cols:
    print(f"Eliminando constantes: {const_cols}")
    df_fe.drop(columns=const_cols, inplace=True, errors="ignore")
    df_fe_test.drop(columns=const_cols, inplace=True, errors="ignore")

print(f"\nDataset final: {df_fe.shape}")
df_fe.to_parquet(PROJECT_ROOT / "data" / "processed" / "features.parquet", index=False)
df_fe_test.to_parquet(PROJECT_ROOT / "data" / "processed" / "features_test.parquet", index=False)

feature_cols = [c for c in df_fe.columns if c not in ["id_cliente", TARGET_COL, "target"]]
with open(PROJECT_ROOT / "data" / "processed" / "feature_list.txt", "w") as f:
    f.write("\n".join(feature_cols))
print(f"✅ features.parquet + features_test.parquet guardados")
print(f"✅ Feature list: {len(feature_cols)} variables")

# ============================================================
# PASO 4 — SPLIT ANTI-LEAKAGE (STRATIFIED 60/20/20)
# ============================================================
print("\n" + "="*65)
print("PASO 4 — SPLIT ANTI-LEAKAGE (Stratified 60/20/20)")
print("="*65)

from sklearn.model_selection import train_test_split

# Columnas para entrenar (excluir IDs, target raw y target)
excl = ["id_cliente", "target", TARGET_COL, ID_ADICIONAL, SUBMISSION_COL]
model_features = [c for c in df_fe.columns if c not in excl]

X = df_fe[model_features]
y = df_fe[TARGET_COL]

# Split 60/20/20
X_train_full, X_test, y_train_full, y_test = train_test_split(
    X, y, test_size=0.20, random_state=RANDOM_STATE, stratify=y
)
X_train, X_val, y_train, y_val = train_test_split(
    X_train_full, y_train_full, test_size=0.25, random_state=RANDOM_STATE, stratify=y_train_full
)

print(f"Train: {X_train.shape[0]:,} ({y_train.mean()*100:.1f}% default)")
print(f"Val:   {X_val.shape[0]:,} ({y_val.mean()*100:.1f}% default)")
print(f"Test:  {X_test.shape[0]:,} ({y_test.mean()*100:.1f}% default)")

# ============================================================
# PASO 5 — PIPELINE DE PREPROCESAMIENTO (FIT SOLO EN TRAIN)
# ============================================================
print("\n" + "="*65)
print("PASO 5 — PREPROCESAMIENTO (Fit solo en Train)")
print("="*65)

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler
from sklearn.impute import SimpleImputer

# Identificar tipos en los datos de train
num_feats = X_train.select_dtypes(include=["int64","float64"]).columns.tolist()
cat_feats = X_train.select_dtypes(include=["object"]).columns.tolist()
print(f"Numéricas para modelo: {len(num_feats)}")
print(f"Categóricas para modelo: {len(cat_feats)}")

num_transformer = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", RobustScaler()),
])

cat_transformer = Pipeline([
    ("imputer", SimpleImputer(strategy="constant", fill_value="Desconocido")),
    ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
])

preprocessor = ColumnTransformer(
    transformers=[
        ("num", num_transformer, num_feats),
        ("cat", cat_transformer, cat_feats),
    ],
    remainder="passthrough",
)

X_train_proc = preprocessor.fit_transform(X_train)
X_val_proc   = preprocessor.transform(X_val)
X_test_proc  = preprocessor.transform(X_test)

# Para submission final
X_sub = df_fe_test[model_features] if all(c in df_fe_test.columns for c in model_features) else df_fe_test[[c for c in model_features if c in df_fe_test.columns]]
# Añadir columnas faltantes como 0
for c in model_features:
    if c not in X_sub.columns:
        X_sub = X_sub.copy()
        X_sub[c] = 0
X_sub = X_sub[model_features]
X_sub_proc = preprocessor.transform(X_sub)

print(f"Features post-preprocesamiento: {X_train_proc.shape[1]}")
print("✅ Preprocesamiento listo — FIT solo en train")

# ============================================================
# PASO 6 — ENTRENAMIENTO DE MODELOS
# ============================================================
print("\n" + "="*65)
print("PASO 6 — ENTRENAMIENTO DE MODELOS")
print("="*65)

from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

pos_weight = (len(y_train) - y_train.sum()) / y_train.sum()
print(f"Peso clase positiva (scale_pos_weight): {pos_weight:.2f}")

# 1. Dummy Baseline
print("\nEntrenando Dummy...")
dummy = DummyClassifier(strategy="stratified", random_state=RANDOM_STATE)
dummy.fit(X_train_proc, y_train)

# 2. Logistic Regression
print("Entrenando Logistic Regression...")
logreg = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1, solver="lbfgs", C=0.5)
logreg.fit(X_train_proc, y_train)

# 3. Random Forest
print("Entrenando Random Forest...")
rf = RandomForestClassifier(n_estimators=300, max_depth=10, class_weight="balanced",
                            random_state=RANDOM_STATE, n_jobs=-1, min_samples_leaf=5)
rf.fit(X_train_proc, y_train)

# 4. HistGradientBoosting (fallback siempre disponible)
print("Entrenando HistGradientBoosting...")
hgb = HistGradientBoostingClassifier(max_iter=400, learning_rate=0.05, max_leaf_nodes=31,
                                      random_state=RANDOM_STATE, class_weight="balanced")
hgb.fit(X_train_proc, y_train)

# 5. LightGBM
try:
    import lightgbm as lgb
    print("Entrenando LightGBM...")
    lgbm = lgb.LGBMClassifier(n_estimators=500, learning_rate=0.03, max_depth=6,
                               num_leaves=31, scale_pos_weight=pos_weight,
                               random_state=RANDOM_STATE, n_jobs=-1, verbosity=-1)
    lgbm.fit(X_train_proc, y_train, eval_set=[(X_val_proc, y_val)],
             callbacks=[lgb.early_stopping(50, verbose=False)])
    lgbm_available = True
except Exception as e:
    print(f"⚠️ LightGBM: {e}")
    lgbm_available = False

# 6. XGBoost
try:
    import xgboost as xgb
    print("Entrenando XGBoost...")
    xgbm = xgb.XGBClassifier(n_estimators=500, learning_rate=0.03, max_depth=6,
                              scale_pos_weight=pos_weight, random_state=RANDOM_STATE,
                              n_jobs=-1, eval_metric="logloss", verbosity=0,
                              early_stopping_rounds=50)
    xgbm.fit(X_train_proc, y_train, eval_set=[(X_val_proc, y_val)], verbose=False)
    xgb_available = True
except Exception as e:
    print(f"⚠️ XGBoost: {e}")
    xgb_available = False

# 7. CatBoost
try:
    from catboost import CatBoostClassifier
    print("Entrenando CatBoost...")
    catb = CatBoostClassifier(iterations=600, learning_rate=0.04, depth=6,
                              auto_class_weights="Balanced", random_seed=RANDOM_STATE,
                              verbose=False, early_stopping_rounds=50)
    catb.fit(X_train_proc, y_train, eval_set=(X_val_proc, y_val), verbose=False)
    cat_available = True
except Exception as e:
    print(f"⚠️ CatBoost: {e}")
    cat_available = False

print("\n✅ Entrenamiento completado")

# ============================================================
# PASO 7 — EVALUACIÓN COMPLETA DE MODELOS
# ============================================================
print("\n" + "="*65)
print("PASO 7 — EVALUACIÓN COMPLETA (10 Métricas)")
print("="*65)

from sklearn.metrics import (
    roc_auc_score, precision_recall_curve, auc, f1_score,
    precision_score, recall_score, log_loss, brier_score_loss,
    confusion_matrix
)

def ks_statistic(y_true, y_proba):
    df_t = pd.DataFrame({"real": np.array(y_true), "proba": y_proba}).sort_values("proba", ascending=False)
    df_t["cum_pos"] = (df_t["real"]==1).cumsum() / max((df_t["real"]==1).sum(), 1)
    df_t["cum_neg"] = (df_t["real"]==0).cumsum() / max((df_t["real"]==0).sum(), 1)
    return float((df_t["cum_pos"] - df_t["cum_neg"]).abs().max())

def lift_top10(y_true, y_proba):
    df_t = pd.DataFrame({"real": np.array(y_true), "proba": y_proba}).sort_values("proba", ascending=False)
    n10 = max(int(len(df_t) * 0.10), 1)
    tasa_top = df_t.head(n10)["real"].mean()
    tasa_global = df_t["real"].mean()
    return float(tasa_top / max(tasa_global, 1e-6))

def evaluar(model, Xtr, ytr, Xva, yva, nombre):
    yp_tr = model.predict_proba(Xtr)[:, 1]
    yp_va = model.predict_proba(Xva)[:, 1]
    yc_va = (yp_va >= 0.5).astype(int)
    p, r, _ = precision_recall_curve(yva, yp_va)
    pr_auc = float(auc(r, p))
    auc_tr = float(roc_auc_score(ytr, yp_tr))
    auc_va = float(roc_auc_score(yva, yp_va))
    return {
        "Modelo": nombre,
        "AUC Train": round(auc_tr, 4),
        "AUC Val": round(auc_va, 4),
        "Gini Val": round(2*auc_va - 1, 4),
        "KS Val": round(ks_statistic(yva, yp_va), 4),
        "PR-AUC Val": round(pr_auc, 4),
        "F1 Val": round(f1_score(yva, yc_va), 4),
        "Recall Val": round(recall_score(yva, yc_va), 4),
        "Precision Val": round(precision_score(yva, yc_va, zero_division=0), 4),
        "Brier Val": round(brier_score_loss(yva, yp_va), 4),
        "Lift@10% Val": round(lift_top10(yva, yp_va), 2),
        "Gap Overfit": round(abs(auc_tr - auc_va), 4),
    }

# Lista de modelos
modelos = [
    (dummy, "Dummy Baseline"),
    (logreg, "Logistic Regression"),
    (rf, "Random Forest"),
    (hgb, "HistGradientBoosting"),
]
if lgbm_available:
    modelos.append((lgbm, "LightGBM"))
if xgb_available:
    modelos.append((xgbm, "XGBoost"))
if cat_available:
    modelos.append((catb, "CatBoost"))

# Evaluar todos
resultados = []
for mod, nom in modelos:
    try:
        res = evaluar(mod, X_train_proc, y_train, X_val_proc, y_val, nom)
        resultados.append(res)
        print(f"  ✅ {nom}: AUC={res['AUC Val']:.4f} | Gini={res['Gini Val']:.4f} | KS={res['KS Val']:.4f} | Gap={res['Gap Overfit']:.4f}")
    except Exception as e:
        print(f"  ❌ {nom}: Error — {e}")

df_exp = pd.DataFrame(resultados)
df_exp.to_csv(PROJECT_ROOT / "reports" / "experiment_log.csv", index=False)

print(f"\n{'='*65}")
print("📋 TABLA COMPARATIVA DE MODELOS:")
print(df_exp[["Modelo","AUC Val","Gini Val","KS Val","Brier Val","Lift@10% Val","Gap Overfit"]].to_string(index=False))

# Seleccionar campeón
df_exp_sorted = df_exp[df_exp["Modelo"] != "Dummy Baseline"].sort_values("AUC Val", ascending=False)
best_name = df_exp_sorted.iloc[0]["Modelo"]
# Build name→model lookup safely (handles unhashable objects)
modelos_dict = {nom: mod for mod, nom in modelos}
best_model = modelos_dict[best_name]
best_metrics = df_exp_sorted.iloc[0]
print(f"\n🏆 CAMPEÓN: {best_name} | AUC={best_metrics['AUC Val']:.4f} | Gini={best_metrics['Gini Val']:.4f} | KS={best_metrics['KS Val']:.4f}")

# ============================================================
# PASO 8 — DIAGNÓSTICO DE EXCELENCIA
# ============================================================
print("\n" + "="*65)
print("PASO 8 — DIAGNÓSTICO DE EXCELENCIA")
print("="*65)

auc_val = best_metrics["AUC Val"]
ks_val = best_metrics["KS Val"]
gap = best_metrics["Gap Overfit"]
gini_val = best_metrics["Gini Val"]
brier_val = best_metrics["Brier Val"]

def nivel_metrica(val, thresholds, labels):
    for t, l in zip(thresholds, labels):
        if val >= t:
            return l
    return labels[-1]

print(f"\n  AUC:   {auc_val:.4f} → {nivel_metrica(auc_val, [0.92,0.83,0.75,0.65], ['EXCELENTE','BUENO','ACEPTABLE','MEDIOCRE'])}")
print(f"  Gini:  {gini_val:.4f} → {nivel_metrica(gini_val, [0.84,0.66,0.50,0.30], ['EXCELENTE','BUENO','ACEPTABLE','MEDIOCRE'])}")
print(f"  KS:    {ks_val:.4f} → {nivel_metrica(ks_val, [0.60,0.50,0.40,0.25], ['EXCELENTE','BUENO','ACEPTABLE','MEDIOCRE'])}")
print(f"  Brier: {brier_val:.4f} → {'BIEN CALIBRADO' if brier_val < 0.18 else 'REVISAR CALIBRACIÓN'}")
print(f"  Gap:   {gap:.4f} → {'✅ BAJO' if gap < 0.05 else ('⚠️ MODERADO' if gap < 0.08 else '❌ ALTO - REGULARIZAR')}")

gate_metricas = auc_val >= 0.75 and ks_val >= 0.30 and gap <= 0.05
print(f"\n  Gate métricas: {'✅ APROBADO' if gate_metricas else '⚠️ POR MEJORAR (continuamos con mejores features disponibles)'}")

# ============================================================
# PASO 9 — CALIBRACIÓN
# ============================================================
print("\n" + "="*65)
print("PASO 9 — CALIBRACIÓN DE PROBABILIDADES")
print("="*65)

from sklearn.calibration import CalibratedClassifierCV, calibration_curve

y_proba_val = best_model.predict_proba(X_val_proc)[:, 1]
brier_raw = brier_score_loss(y_val, y_proba_val)
auc_raw = roc_auc_score(y_val, y_proba_val)

try:
    calibrador = CalibratedClassifierCV(best_model, method="sigmoid", cv="prefit")
    calibrador.fit(X_val_proc, y_val)
    y_proba_cal = calibrador.predict_proba(X_val_proc)[:, 1]
    brier_cal = brier_score_loss(y_val, y_proba_cal)
    auc_cal = roc_auc_score(y_val, y_proba_cal)
    
    usar_calibrado = (brier_cal <= brier_raw) and (auc_cal >= auc_raw - 0.01)
    scoring_model = calibrador if usar_calibrado else best_model
    y_proba_final_val = y_proba_cal if usar_calibrado else y_proba_val
    estado_cal = f"sigmoid ({'APLICADO' if usar_calibrado else 'DESCARTADO - raw mejor'})"
    print(f"  Brier raw: {brier_raw:.4f} | Brier calibrado: {brier_cal:.4f}")
    print(f"  AUC raw: {auc_raw:.4f} | AUC calibrado: {auc_cal:.4f}")
    print(f"  Estado: {estado_cal}")
except Exception as e:
    print(f"  ⚠️ Calibración no aplicada: {e}")
    scoring_model = best_model
    y_proba_final_val = y_proba_val
    estado_cal = "sin_calibrar"

# Gráfico de calibración
try:
    prob_true, prob_pred = calibration_curve(y_val, y_proba_final_val, n_bins=10, strategy="quantile")
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.plot(prob_pred, prob_true, marker="o", color=PALETTE["accent"], linewidth=2, label=f"Modelo ({best_name})")
    ax.plot([0,1],[0,1], linestyle="--", color=PALETTE["neutral"], label="Calibración perfecta")
    ax.fill_between(prob_pred, prob_true, prob_pred, alpha=0.2, color=PALETTE["pos"])
    ax.set_xlabel("Probabilidad predicha (prob_default)")
    ax.set_ylabel("Tasa real de default")
    ax.set_title(f"Curva de Calibración — {best_name}", fontsize=13, fontweight="bold")
    ax.legend()
    ax.grid(True, alpha=0.3)
    save_fig("calibration_curve")
except Exception as e:
    print(f"  ⚠️ No se pudo graficar calibración: {e}")

# ============================================================
# PASO 10 — OPTIMIZACIÓN DEL THRESHOLD Y ROI
# ============================================================
print("\n" + "="*65)
print("PASO 10 — OPTIMIZACIÓN DEL THRESHOLD Y ROI FINANCIERO")
print("="*65)
print("[SUPUESTO] Usando matriz económica de FinanCrece S.A.")
print(f"  VN (buen aprobado):  +${GANANCIA_BUEN_APROBADO}")
print(f"  FP (buen rechazado): ${COSTO_BUEN_RECHAZADO}")
print(f"  FN (default aprobado): ${PERDIDA_DEFAULT_APROBADO}")
print(f"  VP (default rechazado): ${VALOR_DEFAULT_RECHAZADO}")

thresholds = np.linspace(0.05, 0.95, 91)
y_true_val = y_val.values
beneficio_base = (
    int((y_true_val==0).sum()) * GANANCIA_BUEN_APROBADO +
    int((y_true_val==1).sum()) * PERDIDA_DEFAULT_APROBADO
)

resultados_roi = []
for t in thresholds:
    pred = (y_proba_final_val >= t).astype(int)
    buenos = y_true_val == 0
    malos  = y_true_val == 1
    ba = int(((pred==0) & buenos).sum())   # buenos aprobados (VN)
    br = int(((pred==1) & buenos).sum())   # buenos rechazados (FP)
    da = int(((pred==0) & malos).sum())    # defaults aprobados (FN)
    dr = int(((pred==1) & malos).sum())    # defaults rechazados (VP)
    
    beneficio = ba*GANANCIA_BUEN_APROBADO + br*COSTO_BUEN_RECHAZADO + da*PERDIDA_DEFAULT_APROBADO + dr*VALOR_DEFAULT_RECHAZADO
    ahorro = beneficio - beneficio_base
    roi = ahorro / max(abs(beneficio_base), 1)
    
    resultados_roi.append({
        "threshold": round(float(t), 3),
        "buenos_aprobados": ba, "buenos_rechazados": br,
        "defaults_aprobados": da, "defaults_rechazados": dr,
        "beneficio_usd": round(float(beneficio), 0),
        "ahorro_neto_usd": round(float(ahorro), 0),
        "roi_vs_base": round(float(roi), 4),
        "recall_defaults": round(float(dr)/max(da+dr, 1), 4),
        "precision_default": round(float(dr)/max(dr+br, 1), 4) if (dr+br) > 0 else 0,
    })

df_roi = pd.DataFrame(resultados_roi)
df_roi.to_csv(PROJECT_ROOT / "reports" / "threshold_analysis.csv", index=False)

# Threshold óptimo por ROI
opt_idx = df_roi["roi_vs_base"].idxmax()
threshold_opt = df_roi.loc[opt_idx, "threshold"]
roi_opt = df_roi.loc[opt_idx, "roi_vs_base"]
print(f"\n  Threshold óptimo (max ROI): {threshold_opt:.3f}")
print(f"  ROI vs. aprobar todos: {roi_opt*100:.1f}%")
print(f"  Beneficio modelo: ${df_roi.loc[opt_idx,'beneficio_usd']:,.0f}")
print(f"  Ahorro neto: ${df_roi.loc[opt_idx,'ahorro_neto_usd']:,.0f}")

# Gráfico ROI por threshold
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 9))
ax1.plot(df_roi["threshold"], df_roi["roi_vs_base"]*100, color=PALETTE["pos"], linewidth=2.5)
ax1.axvline(x=threshold_opt, color=PALETTE["accent"], linestyle="--", linewidth=2, label=f"Óptimo: {threshold_opt:.3f}")
ax1.axhline(y=0, color=PALETTE["neutral"], linestyle="-", linewidth=1, alpha=0.5)
ax1.fill_between(df_roi["threshold"], df_roi["roi_vs_base"]*100, 0, 
                  where=df_roi["roi_vs_base"]>0, alpha=0.3, color=PALETTE["pos"])
ax1.set_xlabel("Threshold de Rechazo")
ax1.set_ylabel("ROI vs. Aprobar Todos (%)")
ax1.set_title(f"ROI Financiero por Threshold — FinanCrece S.A. [SUPUESTO]", fontsize=13, fontweight="bold")
ax1.legend()
ax1.grid(True, alpha=0.3)

# Breakdown por threshold
ax2.stackplot(df_roi["threshold"],
              df_roi["buenos_aprobados"],
              df_roi["buenos_rechazados"],
              df_roi["defaults_aprobados"],
              df_roi["defaults_rechazados"],
              labels=["Buen Aprobado (VN)", "Buen Rechazado (FP)", "Default Aprobado (FN)", "Default Rechazado (VP)"],
              colors=[PALETTE["neg"], PALETTE["neutral"], PALETTE["pos"], PALETTE["accent"]],
              alpha=0.8)
ax2.axvline(x=threshold_opt, color="white", linestyle="--", linewidth=2)
ax2.set_xlabel("Threshold de Rechazo")
ax2.set_ylabel("N° Clientes")
ax2.set_title("Breakdown Decisiones por Threshold", fontsize=13, fontweight="bold")
ax2.legend(loc="upper left", fontsize=8)
plt.tight_layout()
save_fig("roi_by_threshold")

# ============================================================
# PASO 11 — POLÍTICA DE 3 BANDAS
# ============================================================
print("\n" + "="*65)
print("PASO 11 — POLÍTICA DE 3 BANDAS DE RIESGO")
print("="*65)

# Buscar umbrales óptimos para 3 bandas
# Bajo riesgo: < u_bajo → Aprobar completo
# Medio riesgo: u_bajo a u_alto → Aprobar condicionado 50%
# Alto riesgo: > u_alto → Rechazar
best_roi_3 = -np.inf
best_u_bajo = 0.20
best_u_alto = 0.50

for u_bajo in np.arange(0.15, 0.40, 0.05):
    for u_alto in np.arange(0.40, 0.75, 0.05):
        if u_bajo >= u_alto:
            continue
        bajo = y_proba_final_val < u_bajo
        medio = (y_proba_final_val >= u_bajo) & (y_proba_final_val < u_alto)
        alto = y_proba_final_val >= u_alto
        buenos = y_true_val == 0
        malos = y_true_val == 1
        ben = (
            int((bajo & buenos).sum()) * GANANCIA_BUEN_APROBADO +
            int((bajo & malos).sum()) * PERDIDA_DEFAULT_APROBADO +
            int((medio & buenos).sum()) * GANANCIA_BUEN_APROBADO * FACTOR_EXPOSICION_MEDIA +
            int((medio & malos).sum()) * PERDIDA_DEFAULT_APROBADO * FACTOR_EXPOSICION_MEDIA +
            int((alto & buenos).sum()) * COSTO_BUEN_RECHAZADO +
            int((alto & malos).sum()) * VALOR_DEFAULT_RECHAZADO
        )
        if ben > best_roi_3:
            best_roi_3 = ben
            best_u_bajo = u_bajo
            best_u_alto = u_alto

# Calcular distribución con mejores umbrales
bajo  = y_proba_final_val < best_u_bajo
medio = (y_proba_final_val >= best_u_bajo) & (y_proba_final_val < best_u_alto)
alto  = y_proba_final_val >= best_u_alto
buenos = y_true_val == 0
malos  = y_true_val == 1

politica_3b = {
    "u_bajo": round(float(best_u_bajo), 3),
    "u_alto": round(float(best_u_alto), 3),
    "clientes_bajo": int(bajo.sum()),
    "clientes_medio": int(medio.sum()),
    "clientes_alto": int(alto.sum()),
    "pct_bajo": round(float(bajo.mean()*100), 1),
    "pct_medio": round(float(medio.mean()*100), 1),
    "pct_alto": round(float(alto.mean()*100), 1),
    "tasa_default_bajo": round(float(y_true_val[bajo].mean()), 4) if bajo.sum() > 0 else 0,
    "tasa_default_medio": round(float(y_true_val[medio].mean()), 4) if medio.sum() > 0 else 0,
    "tasa_default_alto": round(float(y_true_val[alto].mean()), 4) if alto.sum() > 0 else 0,
    "beneficio_3_bandas_usd": round(float(best_roi_3), 0),
    "beneficio_base_usd": round(float(beneficio_base), 0),
    "ahorro_vs_base_usd": round(float(best_roi_3 - beneficio_base), 0),
    "decision_bajo": "APROBAR — línea completa",
    "decision_medio": "CONDICIONAR — 50% línea [SUPUESTO]",
    "decision_alto": "RECHAZAR — prevención preventiva",
}

pd.DataFrame([politica_3b]).to_csv(PROJECT_ROOT / "reports" / "politica_3_bandas.csv", index=False)

print(f"\n  Umbrales: bajo < {best_u_bajo:.2f} | medio: {best_u_bajo:.2f}-{best_u_alto:.2f} | alto > {best_u_alto:.2f}")
print(f"\n  {'Banda':<12} {'Clientes':>10} {'%'}>{'':5} {'Default Rate':>15} {'Decisión':<30}")
print(f"  {'-'*75}")
print(f"  {'Bajo Riesgo':<12} {bajo.sum():>10,} {'':>5} {politica_3b['pct_bajo']:>4.1f}% {politica_3b['tasa_default_bajo']*100:>14.1f}%   APROBAR completo")
print(f"  {'Medio Riesgo':<12} {medio.sum():>10,} {'':>5} {politica_3b['pct_medio']:>4.1f}% {politica_3b['tasa_default_medio']*100:>14.1f}%   CONDICIONAR 50% [SUPUESTO]")
print(f"  {'Alto Riesgo':<12} {alto.sum():>10,} {'':>5} {politica_3b['pct_alto']:>4.1f}% {politica_3b['tasa_default_alto']*100:>14.1f}%   RECHAZAR")
print(f"\n  Beneficio política 3 bandas: ${best_roi_3:,.0f}")
print(f"  Ahorro vs. aprobar todos: ${best_roi_3 - beneficio_base:,.0f}")

# Gráfico política 3 bandas
fig, axes = plt.subplots(1, 3, figsize=(16, 6))
bandbands = [bajo, medio, alto]
band_names = ["Bajo Riesgo", "Riesgo Medio", "Alto Riesgo"]
band_colors = [PALETTE["neg"], PALETTE["neutral"], PALETTE["pos"]]
band_rates = [politica_3b["tasa_default_bajo"], politica_3b["tasa_default_medio"], politica_3b["tasa_default_alto"]]
band_counts = [bajo.sum(), medio.sum(), alto.sum()]

for i, (ax, bm, nm, col, dr, cnt) in enumerate(zip(axes, bandbands, band_names, band_colors, band_rates, band_counts)):
    # Histograma de scores en la banda
    scores_banda = y_proba_final_val[bm]
    if len(scores_banda) > 0:
        ax.hist(scores_banda, bins=20, color=col, edgecolor="white", linewidth=0.5, density=True, alpha=0.9)
    ax.set_title(f"{nm}\n{cnt} clientes ({cnt/len(y_true_val)*100:.1f}%)", fontsize=12, fontweight="bold")
    ax.text(0.5, 0.95, f"Default Rate:\n{dr*100:.1f}%", transform=ax.transAxes,
            ha="center", va="top", fontsize=14, fontweight="bold", color=PALETTE["text"],
            bbox=dict(boxstyle="round", facecolor=col, alpha=0.6))
    ax.set_xlabel("prob_default")
    ax.set_ylabel("Densidad")

plt.suptitle(f"FinanCrece S.A. — Política de 3 Bandas\n"
             f"Umbral Bajo: {best_u_bajo:.2f} | Umbral Alto: {best_u_alto:.2f} [SUPUESTO]",
             fontsize=13, fontweight="bold", y=1.02)
plt.tight_layout()
save_fig("politica_3_bandas")

# ============================================================
# PASO 12 — GRÁFICOS DE EVALUACIÓN COMPLETOS
# ============================================================
print("\n" + "="*65)
print("PASO 12 — GRÁFICOS DE EVALUACIÓN")
print("="*65)

from sklearn.metrics import RocCurveDisplay, PrecisionRecallDisplay

fig, axes = plt.subplots(2, 2, figsize=(15, 12))

# 1. Curvas ROC
ax_roc = axes[0, 0]
ax_roc.set_title("Curva ROC (Validación)", color=PALETTE["accent"], fontsize=13, fontweight="bold")
modelos_nodum = [(mod, nom) for mod, nom in modelos if nom != "Dummy Baseline"]
for mod, nom in modelos_nodum:
    try:
        yp = mod.predict_proba(X_val_proc)[:, 1]
        from sklearn.metrics import roc_curve
        fpr, tpr, _ = roc_curve(y_val, yp)
        auc_m = roc_auc_score(y_val, yp)
        ax_roc.plot(fpr, tpr, linewidth=2, label=f"{nom} (AUC={auc_m:.3f})")
    except:
        pass
ax_roc.plot([0,1],[0,1], linestyle="--", color=PALETTE["neutral"], linewidth=1.5, alpha=0.7)
ax_roc.set_xlabel("False Positive Rate")
ax_roc.set_ylabel("True Positive Rate")
ax_roc.legend(fontsize=8)
ax_roc.grid(True, alpha=0.3)

# 2. Curva Precision-Recall
ax_pr = axes[0, 1]
ax_pr.set_title("Curva Precision-Recall (Validación)", color=PALETTE["accent"], fontsize=13, fontweight="bold")
for mod, nom in modelos_nodum:
    try:
        yp = mod.predict_proba(X_val_proc)[:, 1]
        p, r, _ = precision_recall_curve(y_val, yp)
        pr_a = auc(r, p)
        ax_pr.plot(r, p, linewidth=2, label=f"{nom} (PR-AUC={pr_a:.3f})")
    except:
        pass
ax_pr.axhline(y=tasa_default, color=PALETTE["neutral"], linestyle="--", linewidth=1.5, label=f"Baseline ({tasa_default:.2%})")
ax_pr.set_xlabel("Recall")
ax_pr.set_ylabel("Precision")
ax_pr.legend(fontsize=8)
ax_pr.grid(True, alpha=0.3)

# 3. Matriz de confusión del campeón
ax_cm = axes[1, 0]
ax_cm.set_title(f"Matriz de Confusión ({best_name})", color=PALETTE["accent"], fontsize=13, fontweight="bold")
y_pred_best = (y_proba_final_val >= threshold_opt).astype(int)
cm = confusion_matrix(y_val, y_pred_best)
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False, ax=ax_cm,
            xticklabels=["Aprobado (0)", "Rechazado (1)"],
            yticklabels=["Pagador (0)", "Default (1)"], linewidths=0.5)
ax_cm.set_xlabel("Predicción del Modelo")
ax_cm.set_ylabel("Realidad")
for text in ax_cm.texts:
    text.set_color("white" if int(text.get_text()) > cm.max()/2 else "black")

# 4. Lift chart
ax_lift = axes[1, 1]
ax_lift.set_title("Lift Acumulado por Decil", color=PALETTE["accent"], fontsize=13, fontweight="bold")
for mod, nom in modelos_nodum[:4]:
    try:
        yp = mod.predict_proba(X_val_proc)[:, 1]
        df_l = pd.DataFrame({"real": y_val.values, "proba": yp}).sort_values("proba", ascending=False)
        tg = df_l["real"].mean()
        lifts = []
        for d in range(1, 11):
            n = int(len(df_l) * d * 0.1)
            lifts.append(df_l.head(n)["real"].mean() / max(tg, 1e-6))
        ax_lift.plot(range(1, 11), lifts, marker="o", linewidth=2, markersize=4, label=nom)
    except:
        pass
ax_lift.axhline(y=1.0, color=PALETTE["neutral"], linestyle="--", linewidth=1.5, label="Baseline (Lift=1)")
ax_lift.set_xlabel("Decil Acumulado")
ax_lift.set_ylabel("Lift")
ax_lift.legend(fontsize=8)
ax_lift.grid(True, alpha=0.3)

plt.suptitle(f"FinanCrece S.A. — Panel de Evaluación del Modelo (Validación)",
             fontsize=14, fontweight="bold", y=1.02)
plt.tight_layout()
save_fig("model_evaluation_curves")

# ============================================================
# PASO 13 — INTERPRETABILIDAD (SHAP + FEATURE IMPORTANCE)
# ============================================================
print("\n" + "="*65)
print("PASO 13 — INTERPRETABILIDAD")
print("="*65)

# Feature Importance del campeón
feat_imp_df = None
try:
    if hasattr(best_model, "feature_importances_"):
        # Obtener nombres de features post-transformación
        try:
            cat_enc = preprocessor.named_transformers_["cat"].named_steps["encoder"]
            encoded_cat = cat_enc.get_feature_names_out(cat_feats).tolist() if cat_feats else []
        except:
            encoded_cat = [f"cat_{i}" for i in range(len(cat_feats)*5)]
        
        feat_names_proc = num_feats + encoded_cat
        
        # Pad si difieren
        if len(feat_names_proc) < X_train_proc.shape[1]:
            feat_names_proc += [f"remainder_{i}" for i in range(X_train_proc.shape[1] - len(feat_names_proc))]
        feat_names_proc = feat_names_proc[:X_train_proc.shape[1]]
        
        imp = best_model.feature_importances_
        feat_imp_df = pd.DataFrame({"feature": feat_names_proc[:len(imp)], "importance": imp})
        feat_imp_df = feat_imp_df.sort_values("importance", ascending=False).head(30)
        feat_imp_df.to_csv(PROJECT_ROOT / "reports" / "feature_importance.csv", index=False)
        
        # Gráfico
        fig, ax = plt.subplots(figsize=(10, 10))
        top20_imp = feat_imp_df.head(20)
        colors_imp = [PALETTE["pos"] if i < 5 else PALETTE["neg"] for i in range(len(top20_imp))]
        ax.barh(top20_imp["feature"], top20_imp["importance"], color=colors_imp, edgecolor="white", linewidth=0.5)
        ax.set_xlabel("Feature Importance")
        ax.set_title(f"Top 20 Variables — {best_name}", fontsize=14, fontweight="bold")
        ax.invert_yaxis()
        save_fig("feature_importance")
        print(f"✅ Feature importance guardada: {len(feat_imp_df)} features")
        print(f"\nTop 10 features:\n{feat_imp_df.head(10)[['feature','importance']].to_string(index=False)}")
    else:
        print(f"⚠️ {best_name} no tiene feature_importances_, usando LogReg coefficients...")
        imp = np.abs(logreg.coef_[0])
        feat_imp_df = pd.DataFrame({"feature": feat_names_proc[:len(imp)], "importance": imp}).sort_values("importance", ascending=False).head(30)
        feat_imp_df.to_csv(PROJECT_ROOT / "reports" / "feature_importance.csv", index=False)
except Exception as e:
    print(f"⚠️ Feature importance: {e}")

# SHAP
try:
    import shap
    print("\nCalculando SHAP values...")
    
    # Usar muestra si el dataset es grande
    n_shap = min(300, len(X_val_proc))
    X_shap = X_val_proc[:n_shap]
    
    if hasattr(best_model, "predict_proba"):
        explainer = shap.TreeExplainer(best_model) if hasattr(best_model, "tree_") or "Forest" in best_name or "Boosting" in best_name or "GBM" in best_name or "XGB" in best_name or "Cat" in best_name else shap.LinearExplainer(best_model, X_shap)
        shap_values = explainer.shap_values(X_shap)
        
        if isinstance(shap_values, list):
            shap_vals = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        else:
            shap_vals = shap_values
        
        # SHAP summary bar
        fig, ax = plt.subplots(figsize=(10, 8))
        shap_abs_mean = np.abs(shap_vals).mean(axis=0)
        top_idx = np.argsort(shap_abs_mean)[::-1][:20]
        
        try:
            names_shap = feat_names_proc[:shap_vals.shape[1]]
        except:
            names_shap = [f"f_{i}" for i in range(shap_vals.shape[1])]
        
        top_names = [names_shap[i] for i in top_idx]
        top_vals = shap_abs_mean[top_idx]
        
        colors_shap = [PALETTE["pos"] if v > np.median(top_vals) else PALETTE["neg"] for v in top_vals]
        ax.barh(top_names, top_vals, color=colors_shap, edgecolor="white", linewidth=0.3)
        ax.set_xlabel("Mean |SHAP value|")
        ax.set_title(f"SHAP Importance — {best_name}", fontsize=14, fontweight="bold")
        ax.invert_yaxis()
        save_fig("shap_summary")
        print("✅ SHAP calculado")
except Exception as e:
    print(f"⚠️ SHAP: {e} — continuando sin SHAP")

# ============================================================
# PASO 14 — EVALUACIÓN EN TEST INTERNO (60/20/20)
# ============================================================
print("\n" + "="*65)
print("PASO 14 — EVALUACIÓN FINAL EN TEST INTERNO")
print("="*65)

y_proba_test_interno = scoring_model.predict_proba(X_test_proc)[:, 1]
auc_test = roc_auc_score(y_test, y_proba_test_interno)
ks_test = ks_statistic(y_test, y_proba_test_interno)
gini_test = 2*auc_test - 1
brier_test = brier_score_loss(y_test, y_proba_test_interno)
lift_test = lift_top10(y_test, y_proba_test_interno)

p_, r_, _ = precision_recall_curve(y_test, y_proba_test_interno)
prauc_test = auc(r_, p_)

print(f"\n  MÉTRICAS FINALES EN TEST INTERNO ({len(y_test)} clientes):")
print(f"  ROC-AUC:  {auc_test:.4f}")
print(f"  Gini:     {gini_test:.4f}")
print(f"  KS:       {ks_test:.4f}")
print(f"  Brier:    {brier_test:.4f}")
print(f"  PR-AUC:   {prauc_test:.4f}")
print(f"  Lift@10%: {lift_test:.2f}x")
print(f"  Gap (Val vs Test AUC): {abs(best_metrics['AUC Val'] - auc_test):.4f}")

# Guardar predicciones de validación
pred_val_df = pd.DataFrame({
    "id_cliente": df_fe.iloc[X_val.index]["id_cliente"].values if "id_cliente" in df_fe.columns else range(len(y_val)),
    "y_true": y_val.values,
    "prob_default": y_proba_final_val,
    "prediccion_opt": (y_proba_final_val >= threshold_opt).astype(int),
})
pred_val_df.to_csv(PROJECT_ROOT / "reports" / "predicciones_validacion.csv", index=False)

# ============================================================
# PASO 15 — SERIALIZACIÓN DEL MODELO Y METADATA
# ============================================================
print("\n" + "="*65)
print("PASO 15 — SERIALIZACIÓN DEL MODELO")
print("="*65)

joblib.dump(scoring_model, PROJECT_ROOT / "models" / "best_model.joblib")
joblib.dump(preprocessor, PROJECT_ROOT / "models" / "preprocessor.joblib")

metadata = {
    "model_name": best_name,
    "calibration_status": estado_cal,
    "target_col": TARGET_COL,
    "id_cols": ID_COLS,
    "metrica_jurado": METRICA_JURADO,
    "validation_strategy": VALIDATION_STRATEGY,
    "random_state": RANDOM_STATE,
    "threshold_optimal": float(threshold_opt),
    "umbrales_3_bandas": {
        "u_bajo": float(best_u_bajo),
        "u_alto": float(best_u_alto),
    },
    "metricas_val": {
        "roc_auc": float(best_metrics["AUC Val"]),
        "gini": float(best_metrics["Gini Val"]),
        "ks": float(best_metrics["KS Val"]),
        "brier": float(best_metrics["Brier Val"]),
        "pr_auc": float(best_metrics["PR-AUC Val"]),
        "lift_at_10": float(best_metrics["Lift@10% Val"]),
        "overfitting_gap": float(best_metrics["Gap Overfit"]),
    },
    "metricas_test_interno": {
        "roc_auc": round(float(auc_test), 4),
        "gini": round(float(gini_test), 4),
        "ks": round(float(ks_test), 4),
        "brier": round(float(brier_test), 4),
        "pr_auc": round(float(prauc_test), 4),
        "lift_at_10": round(float(lift_test), 2),
    },
    "roi_financiero": {
        "threshold_optimo": float(threshold_opt),
        "roi_vs_base_pct": round(float(roi_opt)*100, 2),
        "beneficio_usd": float(df_roi.loc[opt_idx, "beneficio_usd"]),
        "ahorro_neto_usd": float(df_roi.loc[opt_idx, "ahorro_neto_usd"]),
    },
    "politica_3_bandas": politica_3b,
    "n_features": len(model_features),
    "n_train": len(X_train),
    "n_val": len(X_val),
    "n_test_interno": len(X_test),
    "tasa_default_train": round(float(y_train.mean()), 4),
    "timestamp": datetime.now().isoformat(),
}

with open(PROJECT_ROOT / "models" / "model_metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)

print(f"✅ best_model.joblib guardado")
print(f"✅ preprocessor.joblib guardado")
print(f"✅ model_metadata.json guardado")

# ============================================================
# PASO 16 — SUBMISSION.CSV
# ============================================================
print("\n" + "="*65)
print("PASO 16 — GENERANDO SUBMISSION.CSV")
print("="*65)

y_proba_submission = scoring_model.predict_proba(X_sub_proc)[:, 1]

submission = pd.DataFrame({
    "id_cliente": df_test_raw["id_cliente"].values,
    "prob_default": y_proba_submission,
})

# Verificación de submission
assert len(submission) == len(df_test_raw), "❌ Submission tiene distinto número de filas que test"
assert "id_cliente" in submission.columns, "❌ Falta columna id_cliente"
assert "prob_default" in submission.columns, "❌ Falta columna prob_default"
assert submission["prob_default"].between(0, 1).all(), "❌ Hay probabilidades fuera de [0,1]"
assert submission["id_cliente"].nunique() == len(submission), "❌ IDs duplicados en submission"

submission.to_csv(PROJECT_ROOT / "submission.csv", index=False)
print(f"\n✅ submission.csv generado")
print(f"   Filas: {len(submission):,}")
print(f"   Columnas: {list(submission.columns)}")
print(f"   prob_default stats:")
print(f"     Min: {submission['prob_default'].min():.4f}")
print(f"     Mean: {submission['prob_default'].mean():.4f}")
print(f"     Max: {submission['prob_default'].max():.4f}")
print(f"\nPrimeras 5 filas:")
print(submission.head().to_string(index=False))

# ============================================================
# PASO 17 — CHECKLIST FINAL Y RESUMEN
# ============================================================
print("\n" + "="*65)
print("✅ PIPELINE COMPLETO — RESUMEN FINAL")
print("="*65)

print(f"""
🏦 DATATHON FINANCECRECE — ESAN 2026
{'='*50}
📊 DATOS:
   • Train: {len(df_raw):,} clientes | Test: {len(df_test_raw):,} clientes
   • Tasa default: {tasa_default*100:.1f}% (Desbalance MODERADO)
   • Features: {len(model_features)} variables

🤖 MODELO CAMPEÓN: {best_name}
   • Calibración: {estado_cal}
   • Threshold óptimo: {threshold_opt:.3f} [SUPUESTO matriz económica]

📈 MÉTRICAS (Validación):
   • ROC-AUC:   {best_metrics['AUC Val']:.4f}
   • Gini:      {best_metrics['Gini Val']:.4f}
   • KS:        {best_metrics['KS Val']:.4f}
   • Brier:     {best_metrics['Brier Val']:.4f}
   • Lift@10%:  {best_metrics['Lift@10% Val']:.2f}x
   • Gap:       {best_metrics['Gap Overfit']:.4f}

📈 MÉTRICAS (Test interno):
   • ROC-AUC:   {auc_test:.4f}
   • Gini:      {gini_test:.4f}
   • KS:        {ks_test:.4f}

💰 ROI FINANCIERO [SUPUESTO]:
   • Threshold: {threshold_opt:.3f}
   • ROI vs base: {roi_opt*100:.1f}%
   • Ahorro estimado: ${df_roi.loc[opt_idx,'ahorro_neto_usd']:,.0f}

🎯 POLÍTICA 3 BANDAS [SUPUESTO]:
   • Bajo (<{best_u_bajo:.2f}): {bajo.sum()} clientes | DR={politica_3b['tasa_default_bajo']*100:.1f}%  → APROBAR
   • Medio: {medio.sum()} clientes | DR={politica_3b['tasa_default_medio']*100:.1f}%  → CONDICIONAR 50%
   • Alto (>{best_u_alto:.2f}): {alto.sum()} clientes | DR={politica_3b['tasa_default_alto']*100:.1f}%  → RECHAZAR

📁 ENTREGABLES:
   ✅ submission.csv ({len(submission):,} filas)
   ✅ models/best_model.joblib
   ✅ models/preprocessor.joblib
   ✅ models/model_metadata.json
   ✅ reports/experiment_log.csv
   ✅ reports/threshold_analysis.csv
   ✅ reports/politica_3_bandas.csv
   ✅ reports/feature_importance.csv
   ✅ reports/predicciones_validacion.csv
   ✅ reports/figures/ ({len(list(FIG_DIR.glob('*.png')))} gráficos)
""")

print("🏁 Pipeline completado. Procedemos a generar el Notebook de entrega.")
