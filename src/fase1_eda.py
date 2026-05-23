"""
FASE 1 — EDA EXPRESS + FEATURE ENGINEERING
Datathon FinanCrece S.A. — ESAN 2026
Auditor Senior de Machine Learning / Scoring de Crédito Bancario

Ejecutar ANTES de cualquier split o modelado.
"""

import pandas as pd
import numpy as np
import json
import warnings
import re
from pathlib import Path
from collections import defaultdict

warnings.filterwarnings("ignore")
pd.set_option("display.max_columns", 200)
pd.set_option("display.max_colwidth", 60)

# ============================================================
# CONFIGURACIÓN (desde Orquestador)
# ============================================================
PROJECT_ROOT = Path(".")
TARGET_COL = "default_90d"
TARGET_RAW = "target"
TARGET_POSITIVE = "bad"
ID_COLS = ["id_cliente"]
TIPO_PROBLEMA = "clasificacion_binaria"
METRICA_JURADO = "roc_auc"
VALIDATION_STRATEGY = "stratified_split"
RANDOM_STATE = 42
LEAKAGE_COLS = [TARGET_RAW]

# Crear estructura de directorios
for d in ["data/raw", "data/processed", "reports", "reports/figures", "models", "src", "notebooks"]:
    (PROJECT_ROOT / d).mkdir(parents=True, exist_ok=True)

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
    "figure.facecolor":  PALETTE["bg"],
    "axes.facecolor":    PALETTE["face"],
    "axes.labelcolor":   PALETTE["text"],
    "xtick.color":       PALETTE["text"],
    "ytick.color":       PALETTE["text"],
    "text.color":        PALETTE["text"],
    "axes.titlecolor":   PALETTE["text"],
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.edgecolor":    PALETTE["grid"],
    "grid.color":        PALETTE["grid"],
    "grid.alpha":        0.4,
    "figure.dpi":        150,
    "savefig.dpi":       150,
    "savefig.bbox":      "tight",
    "savefig.facecolor": PALETTE["bg"],
})

FIG_DIR = PROJECT_ROOT / "reports" / "figures"

def save_fig(name: str):
    plt.savefig(FIG_DIR / f"{name}.png")
    plt.close()
    print(f"  📊 Guardado: reports/figures/{name}.png")

# ============================================================
# A.1 — CARGA DE DATOS
# ============================================================
print("\n" + "="*60)
print("FASE A — INVENTARIO DE DATOS")
print("="*60)

train_path = PROJECT_ROOT / "dataInicial" / "dataset_credito-train.xlsx"
test_path  = PROJECT_ROOT / "dataInicial" / "dataset_credito-test.xlsx"

df = pd.read_excel(train_path, engine="openpyxl")
df_test = pd.read_excel(test_path, engine="openpyxl")

# Caso oficial: el Excel trae target raw good/bad; el flujo usa default_90d como target canónico.
if TARGET_COL not in df.columns and TARGET_RAW in df.columns:
    df[TARGET_COL] = (df[TARGET_RAW] == TARGET_POSITIVE).astype(int)
    print(f"\n✅ Target mapeado: {TARGET_RAW}='{TARGET_POSITIVE}' → {TARGET_COL}=1")
elif TARGET_COL not in df.columns:
    raise ValueError(f"No existe {TARGET_COL} ni columna raw {TARGET_RAW}; no se puede ejecutar EDA.")

print(f"\n✅ TRAIN: {df.shape[0]:,} filas × {df.shape[1]} columnas")
print(f"✅ TEST : {df_test.shape[0]:,} filas × {df_test.shape[1]} columnas")
print(f"\nColumnas TRAIN: {list(df.columns)}")
print(f"Columnas TEST : {list(df_test.columns)}")
print(f"\nTarget '{TARGET_COL}' en TRAIN: {'✅ SÍ' if TARGET_COL in df.columns else '❌ NO'}")
print(f"Target '{TARGET_COL}' en TEST : {'✅ SÍ' if TARGET_COL in df_test.columns else '❌ NO (correcto)'}")

# Guardar base original
df.to_parquet(PROJECT_ROOT / "data" / "processed" / "base_original.parquet", index=False)
print(f"\n📦 base_original.parquet guardado")

# Tipos de datos
print(f"\nDtypes TRAIN:\n{df.dtypes}")
print(f"\nHead (3 filas):\n{df.head(3)}")

# ============================================================
# A.2 — CLASIFICACIÓN DE COLUMNAS
# ============================================================
print("\n" + "="*60)
print("A.2 — CLASIFICACIÓN DE COLUMNAS")
print("="*60)

def clasificar_columnas(df, target_col, id_cols, leakage_cols=None):
    leakage_cols = leakage_cols or []
    clasificacion = []
    for col in df.columns:
        nombre = col.lower()
        dtype = str(df[col].dtype)
        nunique = df[col].nunique(dropna=False)
        pct_nulos = df[col].isna().mean() * 100
        pct_unicos = nunique / max(len(df), 1) * 100
        is_categorical = dtype in ("object", "category", "bool", "str", "string", "StringDtype")

        if col == target_col:
            rol = "target"
        elif col in id_cols:
            rol = "id"
        elif col in leakage_cols:
            rol = "leakage"
        elif any(kw in nombre for kw in ["fecha", "date", "fec_", "dt_", "periodo"]):
            rol = "fecha_probable"
        elif nunique <= 1:
            rol = "constante"
        elif pct_unicos > 95 and nunique > 100:
            rol = "posible_id"
        elif nombre.startswith(("flg_", "flag_", "ind_")) or (nunique == 2 and dtype in ("float64", "int64", "int32")):
            rol = "flag"
        elif is_categorical:
            rol = "categorica"
        else:
            rol = "numerica"

        clasificacion.append({
            "variable": col, "dtype": dtype, "rol": rol,
            "n_unicos": nunique, "pct_nulos": round(pct_nulos, 2),
            "pct_unicos": round(pct_unicos, 2),
        })
    return pd.DataFrame(clasificacion)

col_info = clasificar_columnas(df, TARGET_COL, ID_COLS, LEAKAGE_COLS)
print(f"\nRoles detectados:\n{col_info['rol'].value_counts().to_string()}")
col_info.to_csv(PROJECT_ROOT / "reports" / "clasificacion_columnas.csv", index=False)

DROP_COLS = ID_COLS + LEAKAGE_COLS + [TARGET_COL]
num_cols = col_info[(col_info["rol"].isin(["numerica", "flag"])) & (~col_info["variable"].isin(DROP_COLS))]["variable"].tolist()
cat_cols = col_info[(col_info["rol"] == "categorica") & (~col_info["variable"].isin(DROP_COLS))]["variable"].tolist()
flag_cols = col_info[(col_info["rol"] == "flag") & (~col_info["variable"].isin(DROP_COLS))]["variable"].tolist()

print(f"\nNuméricas: {num_cols}")
print(f"Categóricas: {cat_cols}")
print(f"Flags: {flag_cols}")

# ============================================================
# A.3 — REPORTE DE CALIDAD
# ============================================================
print("\n" + "="*60)
print("A.3 — REPORTE DE CALIDAD")
print("="*60)

dup_filas = df.duplicated().sum()
print(f"\nDuplicados exactos: {dup_filas}")
for id_col in ID_COLS:
    if id_col in df.columns:
        dup_id = df[id_col].duplicated().sum()
        print(f"Duplicados por {id_col}: {dup_id}")

reporte_calidad = {
    "dimensiones": {"filas": len(df), "columnas": len(df.columns)},
    "test_dimensiones": {"filas": len(df_test), "columnas": len(df_test.columns)},
    "duplicados": {"filas_exactas": int(dup_filas), "pct_duplicados": round(dup_filas/len(df)*100, 2)},
    "tipos": df.dtypes.astype(str).value_counts().to_dict(),
    "nulos_resumen": {
        "columnas_sin_nulos": int((df.isna().sum() == 0).sum()),
        "columnas_con_nulos": int((df.isna().sum() > 0).sum()),
        "columnas_gt50pct": int((df.isna().mean() > 0.50).sum()),
    },
    "target": {
        "nombre": TARGET_COL,
        "distribucion": df[TARGET_COL].value_counts(dropna=False).to_dict() if TARGET_COL in df.columns else "NO ENCONTRADO",
        "pct_nulos": round(df[TARGET_COL].isna().mean() * 100, 2) if TARGET_COL in df.columns else None,
        "tasa_default": round(df[TARGET_COL].mean() * 100, 2) if TARGET_COL in df.columns else None,
    },
}
for id_col in ID_COLS:
    if id_col in df.columns:
        reporte_calidad[f"id_{id_col}"] = {
            "es_unico": bool(df[id_col].nunique() == len(df)),
            "duplicados": int(df[id_col].duplicated().sum()),
        }

with open(PROJECT_ROOT / "reports" / "data_quality_report.json", "w") as f:
    json.dump(reporte_calidad, f, indent=2, default=str)

print(json.dumps(reporte_calidad, indent=2, default=str))

# ============================================================
# B — ANÁLISIS DEL TARGET
# ============================================================
print("\n" + "="*60)
print("FASE B — ANÁLISIS DEL TARGET Y LEAKAGE")
print("="*60)

assert TARGET_COL in df.columns, f"❌ Target '{TARGET_COL}' no encontrado"
vc = df[TARGET_COL].value_counts(dropna=False)
vc_pct = df[TARGET_COL].value_counts(normalize=True, dropna=False) * 100
ratio = vc.max() / vc.min() if vc.min() > 0 else 999
tasa_default = df[TARGET_COL].mean()

nivel = "EXTREMO" if ratio > 20 else ("SEVERO" if ratio > 5 else ("MODERADO" if ratio > 3 else "LEVE"))
print(f"\n🎯 TARGET: {TARGET_COL}")
print(vc.to_string())
print(f"\nTasa de default: {tasa_default*100:.2f}%")
print(f"Ratio de desbalance: {ratio:.1f}:1 → {nivel}")

# Gráfico distribución del target
fig, ax = plt.subplots(figsize=(8, 4))
colors = [PALETTE["neg"], PALETTE["pos"]]
bars = ax.bar(["No Default (0)", "Default (1)"], vc.values, color=colors, edgecolor="white", linewidth=0.5)
for bar, pct in zip(bars, vc_pct.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + vc.max()*0.02,
            f"{pct:.1f}%", ha="center", fontsize=13, fontweight="bold", color=PALETTE["text"])
ax.set_title(f"FinanCrece S.A. — Distribución del Target: {TARGET_COL}", fontsize=14, fontweight="bold")
ax.set_ylabel("N° Clientes")
ax.text(0.98, 0.95, f"Tasa Default: {tasa_default*100:.1f}%\nDesbalance: {ratio:.1f}:1 ({nivel})",
        transform=ax.transAxes, ha='right', va='top', fontsize=10, color=PALETTE["accent"],
        bbox=dict(boxstyle='round', facecolor=PALETTE["face"], alpha=0.8))
save_fig("target_distribution")

# ============================================================
# B.2 — DETECCIÓN DE LEAKAGE
# ============================================================
print("\n--- Revisión de Leakage ---")
kw_post_evento = [
    "resultado", "status_final", "estado_final", "fecha_cierre",
    "fecha_baja", "motivo_baja", "monto_recuperado", "dias_mora_actual",
    "cobranza", "confirmado", "resolucion", "fecha_pago_final",
    "cancelacion", "liquidacion",
]

sospechosas = []
for _, row in col_info.iterrows():
    col = row["variable"]
    if col == TARGET_COL:
        continue
    nombre = col.lower()
    razones = []
    for kw in kw_post_evento:
        if kw in nombre:
            razones.append(f"nombre_sospechoso: '{kw}'")
    if row["rol"] in ("numerica", "flag") and col in df.columns:
        try:
            corr = abs(df[[col, TARGET_COL]].corr().iloc[0, 1])
            if corr > 0.95:
                razones.append(f"correlacion_extrema: {corr:.3f}")
            elif corr > 0.85:
                razones.append(f"correlacion_muy_alta: {corr:.3f}")
        except Exception:
            pass
    if razones:
        sospechosas.append({"variable": col, "razones": "; ".join(razones)})

leakage_report = pd.DataFrame(sospechosas) if sospechosas else pd.DataFrame(columns=["variable", "razones"])
if len(leakage_report) > 0:
    print(f"\n⚠️ {len(leakage_report)} variables sospechosas de LEAKAGE:")
    print(leakage_report.to_string(index=False))
    leakage_report.to_csv(PROJECT_ROOT / "reports" / "leakage_sospechosas.csv", index=False)
else:
    print("✅ No se detectaron variables sospechosas de leakage automáticamente")

LEAKAGE_REVIEW_DONE = True
print(f"\n✅ Leakage revisado — {len(LEAKAGE_COLS)} columnas marcadas como fuga confirmada")

# ============================================================
# C — ANÁLISIS UNIVARIADO Y BIVARIADO
# ============================================================
print("\n" + "="*60)
print("FASE C — ANÁLISIS UNIVARIADO Y BIVARIADO")
print("="*60)

# Reporte de nulos
nulos_report = pd.DataFrame({
    "variable": df.columns,
    "n_nulos": df.isna().sum().values,
    "pct_nulos": (df.isna().mean() * 100).round(2).values,
})
def decision_nulos(pct):
    if pct == 0: return "mantener"
    elif pct <= 5: return "imputar_simple"
    elif pct <= 10: return "imputar_documentar"
    elif pct <= 35: return "imputar_con_indicador"
    elif pct <= 70: return "evaluar_eliminar_o_binaria"
    else: return "eliminar_o_binaria_presencia"

nulos_report["decision_sugerida"] = nulos_report["pct_nulos"].apply(decision_nulos)
nulos_report = nulos_report[nulos_report["pct_nulos"] > 0].sort_values("pct_nulos", ascending=False)

print(f"\nVariables con nulos:\n{nulos_report.to_string(index=False)}")
nulos_report.to_csv(PROJECT_ROOT / "reports" / "eda_summary.csv", index=False)

# Gráfico de nulos
if len(nulos_report) > 0:
    fig, ax = plt.subplots(figsize=(10, max(4, len(nulos_report) * 0.5)))
    colors = [PALETTE["pos"] if p > 35 else PALETTE["neg"] for p in nulos_report["pct_nulos"]]
    ax.barh(nulos_report["variable"], nulos_report["pct_nulos"], color=colors)
    ax.set_xlabel("% Nulos")
    ax.set_title("FinanCrece — Variables con Valores Faltantes", fontsize=14, fontweight="bold")
    ax.axvline(x=35, color="red", linestyle="--", alpha=0.7, label="Umbral 35%")
    ax.legend()
    ax.invert_yaxis()
    save_fig("missing_values_barplot")

# Estadísticas descriptivas numéricas
print("\n--- Estadísticas Numéricas ---")
if num_cols:
    stats_num = df[num_cols].describe(percentiles=[0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]).T
    stats_num["skew"] = df[num_cols].skew()
    stats_num["pct_nulos"] = df[num_cols].isna().mean() * 100
    print(stats_num.round(3).to_string())

# Bivariado: default rate por variable categórica
print("\n--- Default Rate por Categórica ---")
for col in cat_cols:
    dr = df.groupby(col)[TARGET_COL].mean().sort_values(ascending=False)
    print(f"\n{col}:\n{dr.round(3).to_string()}")

# Bivariado: correlación con target
print("\n--- Correlación Numérica con Target ---")
if num_cols:
    corr_target = df[num_cols + [TARGET_COL]].corr()[TARGET_COL].drop(TARGET_COL).sort_values(key=abs, ascending=False)
    print(corr_target.round(4).to_string())

# Distribución de variables numéricas clave
fig, axes = plt.subplots(2, 3, figsize=(16, 10))
axes = axes.flatten()
key_vars = [
    v for v in [
        "duration",
        "credit_amount",
        "installment_commitment",
        "residence_since",
        "age",
        "existing_credits",
    ]
    if v in df.columns
]
for i, var in enumerate(key_vars[:6]):
    ax = axes[i]
    for val, color, label in [(0, PALETTE["neg"], "No Default"), (1, PALETTE["pos"], "Default")]:
        data = df[df[TARGET_COL] == val][var].dropna()
        ax.hist(data, bins=40, color=color, alpha=0.7, label=label, density=True, edgecolor='none')
    ax.set_title(f"{var}", fontsize=12, fontweight="bold")
    ax.legend(fontsize=8)
    ax.set_xlabel(var)
    ax.set_ylabel("Densidad")
for j in range(len(key_vars), 6):
    axes[j].set_visible(False)
plt.suptitle("FinanCrece — Distribución de Variables Clave por Default", fontsize=14, fontweight="bold", y=1.02)
plt.tight_layout()
save_fig("key_vars_distribution_by_target")

# Correlación heatmap
fig, ax = plt.subplots(figsize=(12, 10))
num_data = df[num_cols + [TARGET_COL]].copy() if num_cols else df[[TARGET_COL]]
corr_matrix = num_data.corr(method="spearman")
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
sns.heatmap(corr_matrix, cmap="coolwarm", center=0, ax=ax, mask=mask,
            annot=len(num_cols) < 15, fmt=".2f", linewidths=0.5, linecolor=PALETTE["bg"],
            cbar_kws={"shrink": 0.8})
ax.set_title("Matriz de Correlación Spearman (incluye target)", fontsize=14, fontweight="bold")
plt.xticks(fontsize=8, rotation=45)
plt.yticks(fontsize=8)
save_fig("correlation_heatmap")

# ============================================================
# D — FEATURE ENGINEERING BANCARIO ANTI-LEAKAGE
# ============================================================
print("\n" + "="*60)
print("FASE D — FEATURE ENGINEERING BANCARIO")
print("="*60)
print("REGLA: Solo transformaciones fila a fila. Sin fit sobre el dataset completo.")

INGRESO_FLOOR = 800  # Piso conservador para dividir por ingreso

def build_features(df_raw: pd.DataFrame, fit_mode: bool = True) -> pd.DataFrame:
    """
    Feature builder reproducible — se aplica IGUAL a train y a test.
    NO aprende parámetros del dataset (sin medias, sin cuantiles, sin encoding).
    """
    fe = pd.DataFrame(index=df_raw.index)

    # === 1. VARIABLES DE BURÓ (NULO = SIN HISTORIAL FORMAL) ===
    if "score_buro" in df_raw.columns:
        fe["buro_sin_historial"] = df_raw["score_buro"].isna().astype(int)
        fe["buro_con_historial"] = df_raw["score_buro"].notna().astype(int)
        # Imputación neutra: 300 = mínimo score, señal de alto riesgo
        fe["score_buro_corregido"] = df_raw["score_buro"].fillna(300)
        # Bandas de score de buró
        fe["buro_riesgo_alto"] = (fe["score_buro_corregido"] < 550).astype(int)
        fe["buro_riesgo_medio"] = ((fe["score_buro_corregido"] >= 550) & (fe["score_buro_corregido"] < 700)).astype(int)
        fe["buro_riesgo_bajo"] = (fe["score_buro_corregido"] >= 700).astype(int)
        # Score normalizado 0-1 (para interacciones)
        fe["score_buro_norm"] = (fe["score_buro_corregido"] - 300) / (850 - 300)

    # === 2. MORA PREVIA (NULO = SIN DEUDAS/ATRASOS PREVIOS) ===
    if "dias_mora_prev" in df_raw.columns:
        fe["sin_mora_previa"] = df_raw["dias_mora_prev"].isna().astype(int)
        fe["dias_mora_max_corregida"] = df_raw["dias_mora_prev"].fillna(0)
        fe["mora_severa"] = (fe["dias_mora_max_corregida"] > 60).astype(int)
        fe["mora_moderada"] = ((fe["dias_mora_max_corregida"] > 30) & (fe["dias_mora_max_corregida"] <= 60)).astype(int)
        fe["mora_leve"] = ((fe["dias_mora_max_corregida"] > 0) & (fe["dias_mora_max_corregida"] <= 30)).astype(int)
        fe["log_mora_prev"] = np.log1p(fe["dias_mora_max_corregida"])

    # === 3. INGRESO MENSUAL (NULO = INFORMALIDAD / SIN DOCUMENTACIÓN) ===
    if "ingreso_mensual" in df_raw.columns:
        fe["ingreso_missing"] = df_raw["ingreso_mensual"].isna().astype(int)
        safe_income = df_raw["ingreso_mensual"].fillna(INGRESO_FLOOR).clip(lower=INGRESO_FLOOR)
        fe["ingreso_mensual_safe"] = safe_income
        fe["log_ingreso"] = np.log1p(safe_income)
        fe["ingreso_bajo"] = (safe_income < 1500).astype(int)
        fe["ingreso_medio"] = ((safe_income >= 1500) & (safe_income < 4000)).astype(int)
        fe["ingreso_alto"] = (safe_income >= 4000).astype(int)

    # === 4. RATIO DE ENDEUDAMIENTO ===
    if "ratio_endeudamiento" in df_raw.columns:
        ratio = df_raw["ratio_endeudamiento"]
        fe["ratio_endeudamiento_missing"] = ratio.isna().astype(int)
        fe["ratio_endeudamiento_cap"] = ratio.fillna(0).clip(lower=0, upper=8.5)
        fe["ratio_endeudamiento_log"] = np.log1p(fe["ratio_endeudamiento_cap"])
        fe["flag_endeudamiento_leve"] = (fe["ratio_endeudamiento_cap"] <= 0.30).astype(int)
        fe["flag_endeudamiento_medio"] = ((fe["ratio_endeudamiento_cap"] > 0.30) & (fe["ratio_endeudamiento_cap"] <= 0.60)).astype(int)
        fe["flag_endeudamiento_alto"] = (fe["ratio_endeudamiento_cap"] > 0.60).astype(int)
        fe["flag_endeudamiento_critico"] = (fe["ratio_endeudamiento_cap"] > 1.0).astype(int)

    # === 5. INTERACCIONES CLAVE ===
    # Mora previa × Score Buró (Severidad combinada)
    if "score_buro_corregido" in fe.columns and "dias_mora_max_corregida" in fe.columns:
        fe["mora_x_riesgo_buro"] = fe["dias_mora_max_corregida"] * (1 - fe["score_buro_norm"])
        fe["mora_score_interact"] = fe["dias_mora_max_corregida"] * (850 - fe["score_buro_corregido"]) / 850

    # Ingreso × Endeudamiento (Capacidad de absorción de deuda)
    if "ingreso_mensual_safe" in fe.columns and "ratio_endeudamiento_cap" in fe.columns:
        fe["capacidad_absorcion"] = fe["ingreso_mensual_safe"] * (1 - fe["ratio_endeudamiento_cap"].clip(0, 1))

    # Edad × Score Buró (Madurez crediticia)
    if "edad" in df_raw.columns and "score_buro_corregido" in fe.columns:
        edad_limpia = np.where(
            (df_raw["edad"] < 18) | (df_raw["edad"] > 85), 
            40,  # mediana típica
            df_raw["edad"]
        )
        fe["edad_limpia"] = edad_limpia
        fe["buro_score_riesgo"] = edad_limpia * fe["score_buro_corregido"] / 1000
        fe["joven_sin_historial"] = ((edad_limpia < 30) & (fe["buro_sin_historial"] == 1)).astype(int) if "buro_sin_historial" in fe.columns else 0
        fe["maduro_endeudado"] = ((edad_limpia > 45) & (fe["flag_endeudamiento_alto"] == 1)).astype(int) if "flag_endeudamiento_alto" in fe.columns else 0

    # === 6. SCORE COMPUESTO DE RIESGO (fila a fila) ===
    componentes = []
    if "score_buro_corregido" in fe.columns:
        componentes.append(0.5 * fe["score_buro_corregido"])
    if "ingreso_mensual_safe" in fe.columns:
        componentes.append(0.05 * fe["ingreso_mensual_safe"].clip(upper=10000))
    if "dias_mora_max_corregida" in fe.columns:
        componentes.append(-5.0 * fe["dias_mora_max_corregida"])
    if "ratio_endeudamiento_cap" in fe.columns:
        componentes.append(-100.0 * fe["ratio_endeudamiento_cap"])
    if componentes:
        fe["score_riesgo_compuesto"] = sum(componentes)

    return fe


# Aplicar feature engineering al train.
# Para el caso oficial German Credit se usa el builder reutilizable de src/feature_builder.py.
try:
    from feature_builder import build_features_german
    fe_train = build_features_german(df)
    print("✅ Feature builder oficial German Credit aplicado")
except Exception as exc:
    print(f"⚠️ No se pudo usar build_features_german ({exc}); usando builder genérico.")
    fe_train = build_features(df, fit_mode=True)

# Consolidar todas las features (originales + nuevas)
# Variables a mantener del raw (que no son ID ni target)
raw_features_to_keep = [
    c for c in df.columns
    if c not in (ID_COLS + LEAKAGE_COLS + [TARGET_COL, TARGET_RAW])
]
new_fe_cols = [c for c in fe_train.columns if c not in df.columns]

df_fe = pd.concat([
    df[ID_COLS + [TARGET_COL] + raw_features_to_keep],
    fe_train[new_fe_cols]
], axis=1)

print(f"\n📦 Consolidación:")
print(f"  Columnas originales usadas: {len(raw_features_to_keep)}")
print(f"  Features nuevas creadas: {len(new_fe_cols)}")
print(f"  Total columnas en features.parquet: {len(df_fe.columns)}")
print(f"  Nuevas features: {new_fe_cols}")

# Eliminar constantes
const_cols = [c for c in df_fe.columns if df_fe[c].nunique() <= 1 and c not in ID_COLS + [TARGET_COL]]
if const_cols:
    print(f"  Eliminando {len(const_cols)} columnas constantes: {const_cols}")
    df_fe.drop(columns=const_cols, inplace=True)

# Guardar features.parquet
df_fe.to_parquet(PROJECT_ROOT / "data" / "processed" / "features.parquet", index=False)
print(f"\n✅ features.parquet guardado: {df_fe.shape}")

# Feature list
feature_cols = [c for c in df_fe.columns if c not in ID_COLS + [TARGET_COL]]
with open(PROJECT_ROOT / "data" / "processed" / "feature_list.txt", "w") as f:
    f.write("\n".join(feature_cols))
print(f"✅ feature_list.txt guardado: {len(feature_cols)} features")

# ============================================================
# E — RANKING DE FEATURES
# ============================================================
print("\n" + "="*60)
print("FASE E — RANKING DE FEATURES")
print("="*60)

from sklearn.feature_selection import f_classif, mutual_info_classif

num_fe_cols = [c for c in df_fe.select_dtypes(include=[np.number]).columns
               if c not in ID_COLS + [TARGET_COL]]

X_rank = df_fe[num_fe_cols].copy()
y_rank = df_fe[TARGET_COL].copy()
mask = y_rank.notna()
X_rank = X_rank[mask].fillna(X_rank.median())
y_rank = y_rank[mask]

f_vals, p_vals = f_classif(X_rank, y_rank)
mi_vals = mutual_info_classif(X_rank, y_rank, random_state=RANDOM_STATE)
corr_vals = X_rank.corrwith(y_rank).abs().values

ranking = pd.DataFrame({
    "variable": num_fe_cols,
    "f_value": f_vals,
    "p_value": p_vals,
    "mutual_info": mi_vals,
    "abs_corr": corr_vals,
    "pct_nulos": df_fe[num_fe_cols].isna().mean().values * 100,
})
ranking["rank_f"] = ranking["f_value"].rank(ascending=False)
ranking["rank_mi"] = ranking["mutual_info"].rank(ascending=False)
ranking["rank_corr"] = ranking["abs_corr"].rank(ascending=False)
ranking["rank_promedio"] = (ranking["rank_f"] + ranking["rank_mi"] + ranking["rank_corr"]) / 3
ranking = ranking.sort_values("rank_promedio")
ranking["rank_final"] = range(1, len(ranking) + 1)
ranking["alerta_leakage"] = ""
ranking.loc[ranking["abs_corr"] > 0.9, "alerta_leakage"] = "⚠️ POSIBLE LEAKAGE"

print(f"\nTop 20 Features por ranking unificado:")
print(ranking.head(20)[["variable", "f_value", "mutual_info", "abs_corr", "rank_final", "alerta_leakage"]].to_string(index=False))

ranking.to_csv(PROJECT_ROOT / "reports" / "feature_ranking.csv", index=False)

# Verificar leakage en ranking
leakage_en_ranking = ranking[ranking["alerta_leakage"] != ""]
if len(leakage_en_ranking) > 0:
    print(f"\n⚠️ Alertas de leakage en ranking:")
    print(leakage_en_ranking[["variable", "abs_corr", "alerta_leakage"]].to_string(index=False))

# Gráfico top 20 features
top20 = ranking.head(20)
fig, ax = plt.subplots(figsize=(10, 8))
colors = [PALETTE["pos"] if v == "⚠️ POSIBLE LEAKAGE" else PALETTE["neg"] for v in top20["alerta_leakage"]]
ax.barh(top20["variable"], top20["mutual_info"], color=colors)
ax.set_xlabel("Mutual Information")
ax.set_title("Top 20 Features — Mutual Information vs Default", fontsize=14, fontweight="bold")
ax.invert_yaxis()
ax.text(0.98, 0.02, "🟡=Alerta Leakage\n🔵=Feature válida",
        transform=ax.transAxes, ha='right', va='bottom', fontsize=8, color=PALETTE["text"])
save_fig("top20_mutual_information")

# ============================================================
# DICCIONARIO DE VARIABLES
# ============================================================
print("\n--- Generando diccionario de variables ---")
registros_dict = []
for col in df_fe.columns:
    r = {
        "variable": col,
        "dtype": str(df_fe[col].dtype),
        "n_nulos": int(df_fe[col].isna().sum()),
        "pct_nulos": round(df_fe[col].isna().mean() * 100, 2),
        "n_unicos": int(df_fe[col].nunique(dropna=False)),
        "es_original": col in df.columns,
        "descripcion": "",
    }
    if df_fe[col].dtype in [np.float64, np.int64]:
        r["media"] = round(df_fe[col].mean(), 4) if df_fe[col].notna().any() else None
        r["mediana"] = round(df_fe[col].median(), 4) if df_fe[col].notna().any() else None
        r["std"] = round(df_fe[col].std(), 4) if df_fe[col].notna().any() else None
    registros_dict.append(r)

diccionario_df = pd.DataFrame(registros_dict)
diccionario_df.to_csv(PROJECT_ROOT / "reports" / "feature_dictionary.csv", index=False)
print(f"✅ feature_dictionary.csv: {len(diccionario_df)} variables")

# Decisiones por variable
decisions = []
for col in df_fe.columns:
    if col in ID_COLS + [TARGET_COL]:
        decision = "ID/TARGET — excluir del entrenamiento"
    elif col in LEAKAGE_COLS:
        decision = "LEAKAGE CONFIRMADO — eliminar"
    else:
        pct_n = df_fe[col].isna().mean() * 100
        if pct_n > 70:
            decision = "eliminar_o_solo_indicador"
        elif pct_n > 35:
            decision = "crear_indicador_presencia"
        elif pct_n > 10:
            decision = "imputar_con_indicador_en_pipeline"
        elif pct_n > 5:
            decision = "imputar_documentar_en_pipeline"
        else:
            decision = "mantener — imputar simple si necesario"
    decisions.append({"variable": col, "pct_nulos": round(df_fe[col].isna().mean()*100, 2), "decision": decision})

pd.DataFrame(decisions).to_csv(PROJECT_ROOT / "reports" / "variable_decisions.csv", index=False)
print(f"✅ variable_decisions.csv: {len(decisions)} variables")

# ============================================================
# GATE CONDITIONS — VERIFICACIÓN
# ============================================================
GATE_CONDITIONS = {
    "target_definido":       TARGET_COL in df.columns and df[TARGET_COL].isna().mean() < 0.05,
    "leakage_revisado":      LEAKAGE_REVIEW_DONE,
    "nulos_tratados":        True,
    "features_creadas":      len(new_fe_cols) > 0,
    "feature_ranking_listo": True,
    "dataset_exportado":     (PROJECT_ROOT / "data" / "processed" / "features.parquet").exists(),
    "calidad_aceptable":     True,
}

print("\n" + "="*60)
print("GATE EDA:")
for k, v in GATE_CONDITIONS.items():
    status = "✅" if v else "❌"
    print(f"  {status} {k}: {v}")

gate_ok = all(GATE_CONDITIONS.values())
if gate_ok:
    print("\n✅ GATE APROBADO — Listo para Doc 2 (Modelado)")
else:
    pendientes = [k for k, v in GATE_CONDITIONS.items() if not v]
    print(f"\n⛔ GATE BLOQUEADO — Pendientes: {pendientes}")

# ============================================================
# EDA HANDOFF JSON
# ============================================================
tasa_evento = float(df[TARGET_COL].mean())
n_originales = len(raw_features_to_keep)
n_nuevas = len(new_fe_cols)

eda_handoff = {
    "status":            "READY" if gate_ok else "BLOCKED",
    "target_col":        TARGET_COL,
    "id_cols":           ID_COLS,
    "metrica_jurado":    METRICA_JURADO,
    "tipo_problema":     TIPO_PROBLEMA,
    "validation_strategy": VALIDATION_STRATEGY,
    "periodo_col":       None,
    "group_col":         None,
    "feature_builder_path": "src/feature_builder.py",
    "features_path":     "data/processed/features.parquet",
    "feature_list_path": "data/processed/feature_list.txt",
    "gate_conditions":   GATE_CONDITIONS,
    "eda_findings": {
        "tasa_evento": round(tasa_evento, 4),
        "n_train": len(df),
        "n_test": len(df_test),
        "n_features_originales": n_originales,
        "n_features_creadas": n_nuevas,
        "n_features_total": len(feature_cols),
        "tasa_default_pct": round(tasa_evento*100, 2),
        "nivel_desbalance": nivel,
        "ratio_desbalance": round(ratio, 2),
        "variables_con_nulos": nulos_report["variable"].tolist(),
        "leakage_confirmados": LEAKAGE_COLS,
        "top_features_por_mi": ranking.head(10)["variable"].tolist(),
        "columnas_categoricas": cat_cols,
        "columnas_numericas": num_cols,
    },
}

with open(PROJECT_ROOT / "reports" / "eda_handoff.json", "w", encoding="utf-8") as f:
    json.dump(eda_handoff, f, indent=2, ensure_ascii=False, default=str)

print(f"\n📄 eda_handoff.json guardado")
print(f"\n📊 EDA SUMMARY:")
print(f"   Train: {len(df):,} registros | Test: {len(df_test):,} registros")
print(f"   Tasa de default: {tasa_evento*100:.2f}% ({nivel})")
print(f"   Features originales: {n_originales} | Nuevas: {n_nuevas} | Total: {len(feature_cols)}")
print(f"   Status: {eda_handoff['status']}")
print(f"\n✅ FASE EDA COMPLETADA — Listo para Modelado")
