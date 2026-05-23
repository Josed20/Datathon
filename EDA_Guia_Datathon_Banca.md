# 📊 Guía Técnica de EDA — Sistema de Documentos para Datathon

> **Documento 1 de 3** | Se complementa con: `Modelado_Validacion_Datathon_Banca.md` (Doc 2) y `ORQUESTADOR_DATATHON.md` (Doc 3 — Flujo Principal)

---

## 0. INTERFAZ CON EL ORQUESTADOR

### 0.1 Entradas que este documento espera (INPUTS)

El Orquestador (`ORQUESTADOR_DATATHON.md`) debe proveer la siguiente información antes de iniciar el EDA:

| Input | Ejemplo | Obligatorio |
|---|---|:---:|
| `TARGET_COL` | `"CHURN"` | ✅ |
| `TIPO_PROBLEMA` | `"clasificacion_binaria"` | ✅ |
| `METRICA_JURADO` | `"roc_auc"` | ✅ |
| `DATA_PATHS` | `["data/raw/BASE.sav"]` | ✅ |
| `ID_COLS` | `["ID_CLIENTE"]` | ✅ |
| `CONTEXTO_NEGOCIO` | `"Predecir fuga de clientes..."` | ✅ |
| `VALIDATION_STRATEGY` | `"stratified_split"` | ✅ |
| `PERIODO_COL` | `"PERIODO"` | ❌ |
| `GROUP_COL` | `"ID_CLIENTE"` | ❌ |
| `DATE_COLS` | `["FECHA_ALTA"]` | ❌ |
| `RESTRICCIONES` | `["no usar variable X"]` | ❌ |
| `DICCIONARIO_EXTERNO` | `"data/raw/diccionario.xlsx"` | ❌ |
| `FEATURE_BUILDER_PATH` | `"src/feature_builder.py"` | ❌ |

```python
# --- BLOQUE DE CONFIGURACIÓN (lo llena el Orquestador) ---
from pathlib import Path

PROJECT_ROOT   = Path(".")
TARGET_COL     = "default_90d"
TIPO_PROBLEMA  = "clasificacion_binaria"
METRICA_JURADO = "roc_auc"
DATA_PATHS     = [PROJECT_ROOT / "dataInicial" / "clientes_entrenamiento.csv"]
ID_COLS        = ["id_cliente"]
VALIDATION_STRATEGY = "temporal_split"  # ideal para solicitudes 2022-2024 vs 2026 de test
PERIODO_COL    = None
GROUP_COL      = None
DATE_COLS      = []
LEAKAGE_COLS   = []                  # variables marcadas como fuga por el Orquestador
LEAKAGE_REVIEW_DONE = True          # Verificado: sin variables de fuga obvias
FEATURE_BUILDER_PATH = PROJECT_ROOT / "src" / "feature_builder.py"
RANDOM_STATE   = 42
```

**Frontera con Doc 2:** este EDA puede crear features fila a fila, indicadores de missing y reportes exploratorios. El split, la imputacion, el encoding, el escalado, la winsorizacion aprendida de cuantiles y cualquier seleccion final que use validacion pertenecen al Doc 2 y se ajustan solo con train.

### 0.2 Salidas que este documento produce (OUTPUTS)

| Artefacto | Ruta | Descripción |
|---|---|---|
| Dataset de features | `data/processed/features.parquet` | Features reproducibles + IDs requeridos + target; puede conservar nulos |
| Base original de referencia | `data/processed/base_original.parquet` | Datos sin FE usados como punto de comparacion |
| Lista de features | `data/processed/feature_list.txt` | Predictors entregados al Doc 2 |
| Resumen EDA | `reports/eda_summary.csv` | Métricas por variable |
| Diccionario de features | `reports/feature_dictionary.csv` | Nombre, tipo, origen, descripción |
| Decisiones por variable | `reports/variable_decisions.csv` | Mantener, eliminar, transformar o revisar |
| Reporte de calidad | `reports/data_quality_report.json` | Nulos, duplicados, target y dimensiones |
| Figuras | `reports/figures/*.png` | Gráficos del EDA |
| Feature ranking | `reports/feature_ranking.csv` | Ranking exploratorio; no es seleccion final por validacion |
| Informe para Orquestador | `reports/eda_handoff.json` | Metadatos para Doc 2 |
| Feature builder | `src/feature_builder.py` | Transformaciones fila a fila reutilizables para train/test si hay submission |

### 0.3 Condiciones de puerta (GATE CONDITIONS)

El EDA **NO debe pasar al modelado** (Doc 2) hasta cumplir **todas** estas condiciones:

```python
GATE_CONDITIONS = {
    "target_definido":       False,  # Target confirmado y validado
    "leakage_revisado":      False,  # Variables de fuga identificadas y removidas
    "nulos_tratados":        False,  # Decisión documentada; imputacion se ajusta en Doc 2
    "features_creadas":      False,  # Al menos 1 ronda de feature engineering
    "feature_ranking_listo": False,  # Ranking estadístico completado
    "dataset_exportado":     False,  # features.parquet generado
    "calidad_aceptable":     False,  # Sin columnas >95% nulos sin tratamiento
}

def verificar_gate():
    pendientes = [k for k, v in GATE_CONDITIONS.items() if not v]
    if pendientes:
        print(f"⛔ GATE BLOQUEADO — Pendientes: {pendientes}")
        return False
    print("✅ GATE APROBADO — Listo para Doc 2 (Modelado)")
    return True
```

---

## FASE A — Inventario de Datos y Evaluación de Calidad

### A.1 Setup inicial y carga de datos

```python
import pandas as pd
import numpy as np
import re
import json
import warnings
from pathlib import Path
from collections import defaultdict

warnings.filterwarnings("ignore")
pd.set_option("display.max_columns", 200)
pd.set_option("display.max_colwidth", 60)

# --- Estructura de directorios ---
for d in ["data/raw", "data/processed", "reports", "reports/figures", "models", "src"]:
    (PROJECT_ROOT / d).mkdir(parents=True, exist_ok=True)

# --- Carga multi-formato ---
def load_data(path: Path) -> tuple:
    """Carga datos con soporte para .sav (SPSS), .xlsx, .csv, .parquet, .json."""
    ext = path.suffix.lower()
    meta = None
    if ext == ".sav":
        import pyreadstat
        df, meta = pyreadstat.read_sav(str(path))
        print(f"  ℹ️ SPSS: {len(meta.column_names_to_labels)} etiquetas detectadas")
    elif ext == ".xlsx":
        df = pd.read_excel(path, engine="openpyxl")
    elif ext == ".xls":
        df = pd.read_excel(path)
    elif ext == ".csv":
        try:
            df = pd.read_csv(path)
        except UnicodeDecodeError:
            df = pd.read_csv(path, encoding="latin-1", sep=";")
    elif ext == ".parquet":
        df = pd.read_parquet(path)
    elif ext in (".json", ".jsonl"):
        df = pd.read_json(path, lines=(ext == ".jsonl"))
    else:
        raise ValueError(f"Formato no soportado: {ext}")
    print(f"  ✅ Cargado: {path.name} → {df.shape[0]:,} filas × {df.shape[1]} columnas")
    return df, meta

# --- Cargar todos los archivos ---
dataframes = {}
spss_meta = {}
for p in DATA_PATHS:
    df_loaded, meta_loaded = load_data(p)
    dataframes[p.stem] = df_loaded
    if meta_loaded:
        spss_meta[p.stem] = meta_loaded

# Si hay un solo archivo:
df = list(dataframes.values())[0]
```

### A.2 Extraer etiquetas SPSS (si aplica)

Los archivos `.sav` de bancos latinoamericanos contienen etiquetas descriptivas que sirven como diccionario:

```python
def extraer_etiquetas_spss(meta) -> pd.DataFrame:
    """Extrae etiquetas de columnas y valores desde metadatos SPSS."""
    labels = []
    for col in meta.column_names:
        label = meta.column_names_to_labels.get(col, "")
        val_labels = meta.variable_value_labels.get(col, {})
        labels.append({
            "variable": col,
            "etiqueta_spss": label,
            "valores_etiquetados": str(val_labels) if val_labels else "",
        })
    return pd.DataFrame(labels)

if spss_meta:
    etiquetas_spss = extraer_etiquetas_spss(list(spss_meta.values())[0])
    etiquetas_spss.to_csv(PROJECT_ROOT / "reports" / "etiquetas_spss.csv", index=False)
```

### A.3 Auto-clasificación de columnas

```python
def clasificar_columnas(df, target_col, id_cols, date_cols=None, leakage_cols=None):
    """
    Clasifica cada columna en roles: target, id, fecha, leakage,
    flag, categorica, numerica, constante.
    """
    date_cols = date_cols or []
    leakage_cols = leakage_cols or []
    clasificacion = []

    for col in df.columns:
        nombre = col.lower()
        dtype = str(df[col].dtype)
        nunique = df[col].nunique(dropna=False)
        pct_nulos = df[col].isna().mean() * 100
        pct_unicos = nunique / max(len(df), 1) * 100

        # Determinar rol
        if col == target_col:
            rol = "target"
        elif col in id_cols:
            rol = "id"
        elif col in leakage_cols:
            rol = "leakage"
        elif col in date_cols or dtype == "datetime64[ns]":
            rol = "fecha"
        elif any(kw in nombre for kw in ["fecha", "date", "fec_", "dt_"]):
            rol = "fecha_probable"
        elif nunique <= 1:
            rol = "constante"
        elif pct_unicos > 95 and nunique > 100:
            rol = "posible_id"
        elif nombre.startswith(("flg_", "flag_", "ind_")) or nunique == 2:
            if dtype in ("float64", "int64", "int32", "float32"):
                rol = "flag"
            else:
                rol = "categorica"
        elif dtype in ("object", "category", "bool"):
            rol = "categorica"
        else:
            rol = "numerica"

        clasificacion.append({
            "variable": col,
            "dtype": dtype,
            "rol": rol,
            "n_unicos": nunique,
            "pct_nulos": round(pct_nulos, 2),
            "pct_unicos": round(pct_unicos, 2),
        })

    return pd.DataFrame(clasificacion)

col_info = clasificar_columnas(df, TARGET_COL, ID_COLS, DATE_COLS, LEAKAGE_COLS)
print(col_info["rol"].value_counts())
col_info.to_csv(PROJECT_ROOT / "reports" / "clasificacion_columnas.csv", index=False)
```

### A.4 Detección de familias temporales de columnas

En datasets bancarios es muy común encontrar familias de columnas como `CANAL1_0`, `CANAL1_1`, ..., `CANAL1_5` que representan periodos (ej: 6 meses). También patrones como `SDO_CTA_0`, `SDO_CTA_1`, etc. para saldos.

```python
def detectar_familias_temporales(columns, min_miembros=3):
    """
    Detecta familias de columnas con sufijo numérico (ej: CANAL1_0..CANAL1_5).
    Retorna dict {prefijo: [lista de columnas ordenadas]}.
    """
    familias = defaultdict(list)
    for col in columns:
        match = re.match(r"^(.+?)_(\d+)$", col)
        if match:
            prefijo, idx = match.groups()
            familias[prefijo].append((int(idx), col))

    # Filtrar y ordenar
    resultado = {}
    for prefijo, miembros in familias.items():
        if len(miembros) >= min_miembros:
            miembros_sorted = sorted(miembros, key=lambda x: x[0])
            resultado[prefijo] = [col for _, col in miembros_sorted]

    return resultado

familias = detectar_familias_temporales(df.columns)
print(f"\n📦 Familias temporales detectadas: {len(familias)}")
for pref, cols in familias.items():
    print(f"  {pref}: {len(cols)} periodos → {cols[0]}...{cols[-1]}")
```

### A.5 Patrones bancarios comunes

El agente debe reconocer estos prefijos frecuentes en datos bancarios:

| Prefijo/Patrón | Significado típico | Ejemplo |
|---|---|---|
| `CANAL*_N` | Transacciones por canal en periodo N | `CANAL1_0` = cajero mes 0 |
| `SDO_*` | Saldo (Saldo Deudor u Operativo) | `SDO_CTA_3` = saldo cuenta mes 3 |
| `FLG_*` / `FLAG_*` | Bandera binaria (0/1) | `FLG_NOMINA` = tiene nómina |
| `IND_*` | Indicador binario | `IND_TC` = tiene tarjeta crédito |
| `NRO_*` / `NUM_*` | Conteo | `NRO_PRODUCTOS` = # de productos |
| `MTO_*` / `MONTO_*` | Monto monetario | `MTO_DEBITO` = monto de débitos |
| `RENT_*` | Rentabilidad | `RENT_TOTAL` = rentabilidad total |
| `PERIODO` | Fecha en formato YYYYMM | `201408` = agosto 2014 |
| `ANTIGUEDAD*` | Antigüedad en meses/años | `ANTIGUEDAD_MESES` |

### A.6 Evaluación de calidad — Reporte completo

```python
def generar_reporte_calidad(df, target_col, id_cols):
    """Genera reporte completo de calidad de datos."""
    reporte = {
        "dimensiones": {"filas": len(df), "columnas": len(df.columns)},
        "duplicados": {
            "filas_exactas": int(df.duplicated().sum()),
            "pct_duplicados": round(df.duplicated().mean() * 100, 2),
        },
        "tipos": df.dtypes.astype(str).value_counts().to_dict(),
        "nulos_resumen": {
            "columnas_sin_nulos": int((df.isna().sum() == 0).sum()),
            "columnas_con_nulos": int((df.isna().sum() > 0).sum()),
            "columnas_gt50pct": int((df.isna().mean() > 0.50).sum()),
            "columnas_gt95pct": int((df.isna().mean() > 0.95).sum()),
        },
        "target": {
            "nombre": target_col,
            "distribucion": df[target_col].value_counts(dropna=False).to_dict()
                if target_col in df.columns else "NO ENCONTRADO",
            "pct_nulos": round(df[target_col].isna().mean() * 100, 2)
                if target_col in df.columns else None,
        },
    }

    # IDs
    for id_col in id_cols:
        if id_col in df.columns:
            reporte[f"id_{id_col}"] = {
                "es_unico": bool(df[id_col].nunique() == len(df)),
                "duplicados": int(df[id_col].duplicated().sum()),
            }

    return reporte

reporte_calidad = generar_reporte_calidad(df, TARGET_COL, ID_COLS)
with open(PROJECT_ROOT / "reports" / "data_quality_report.json", "w") as f:
    json.dump(reporte_calidad, f, indent=2, default=str)

print(json.dumps(reporte_calidad, indent=2, default=str))
```

### A.7 Checkpoint Fase A

```python
# Verificar condiciones mínimas para continuar
assert TARGET_COL in df.columns, f"❌ Target '{TARGET_COL}' no encontrado"
assert df[TARGET_COL].isna().mean() < 0.05, "❌ Target tiene >5% nulos"
assert df.shape[0] > 100, "❌ Dataset demasiado pequeño"
print("✅ Fase A completada — Inventario y calidad verificados")
```

---

## FASE B — Análisis del Target y Comprensión de Negocio

### B.1 Setup visual (dark mode)

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns

PALETTE = {
    "pos": "#F5A623", "neg": "#2D6DB5",
    "bg": "#0A1628", "text": "#FFFFFF",
    "grid": "#1E3A5F", "face": "#0D1F38",
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
```

### B.2 Distribución y desbalance del target

```python
def analizar_target(df, target_col, tipo_problema):
    """Analiza la variable objetivo según el tipo de problema."""
    print(f"\n{'='*60}")
    print(f"TARGET: {target_col} | TIPO: {tipo_problema}")
    print(f"{'='*60}")

    if tipo_problema in ("clasificacion_binaria", "multiclase"):
        vc = df[target_col].value_counts(dropna=False)
        vc_pct = df[target_col].value_counts(normalize=True, dropna=False) * 100
        print(vc)
        print(f"\nTasa de clase positiva: {vc_pct.min():.2f}%")

        ratio = vc.max() / vc.min()
        if ratio > 20:
            nivel = "EXTREMO"
        elif ratio > 5:
            nivel = "SEVERO"
        elif ratio > 3:
            nivel = "MODERADO"
        else:
            nivel = "LEVE"
        print(f"Ratio de desbalance: {ratio:.1f}:1 → {nivel}")

        # Gráfico
        fig, ax = plt.subplots(figsize=(8, 4))
        colors = [PALETTE["neg"], PALETTE["pos"]] if len(vc) == 2 else sns.color_palette("viridis", len(vc))
        bars = ax.bar(vc.index.astype(str), vc.values, color=colors, edgecolor="white", linewidth=0.5)
        for bar, pct in zip(bars, vc_pct.values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + vc.max()*0.02,
                    f"{pct:.1f}%", ha="center", fontsize=12, fontweight="bold")
        ax.set_title(f"Distribución del Target: {target_col}", fontsize=14, fontweight="bold")
        ax.set_ylabel("Frecuencia")
        save_fig("target_distribution")

        return {"ratio_desbalance": round(ratio, 2), "nivel": nivel, "tasa_positiva": round(vc_pct.min(), 2)}

    elif tipo_problema == "regresion":
        stats = df[target_col].describe()
        print(stats)
        skew = df[target_col].skew()
        print(f"Asimetría: {skew:.3f}")

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        axes[0].hist(df[target_col].dropna(), bins=50, color=PALETTE["pos"], edgecolor="white", linewidth=0.3)
        axes[0].set_title(f"Distribución: {target_col}")
        axes[1].boxplot(df[target_col].dropna(), vert=True)
        axes[1].set_title(f"Boxplot: {target_col}")
        save_fig("target_distribution")

        return {"skew": round(skew, 3), "stats": stats.to_dict()}

target_info = analizar_target(df, TARGET_COL, TIPO_PROBLEMA)
```

### B.3 Detección automática de leakage

> ⚠️ **REGLA CRÍTICA**: Toda variable que sea consecuencia del evento objetivo o que contenga información posterior al momento de predicción es **fuga de información** y debe eliminarse ANTES de cualquier análisis.

```python
def detectar_leakage(df, target_col, col_info_df):
    """
    Identifica variables con alta probabilidad de ser leakage.
    Retorna lista de columnas sospechosas con justificación.
    """
    sospechosas = []

    for _, row in col_info_df.iterrows():
        col = row["variable"]
        if col == target_col:
            continue

        nombre = col.lower()
        razones = []

        # 1. Nombres sospechosos
        kw_post_evento = [
            "resultado", "status_final", "estado_final", "fecha_cierre",
            "fecha_baja", "motivo_baja", "monto_recuperado", "dias_mora_actual",
            "cobranza", "confirmado", "resolucion", "fecha_pago_final",
            "cancelacion", "liquidacion",
        ]
        for kw in kw_post_evento:
            if kw in nombre:
                razones.append(f"nombre_sospechoso: contiene '{kw}'")

        # 2. Correlación perfecta o casi perfecta con target
        if row["rol"] in ("numerica", "flag") and col in df.columns:
            try:
                corr = abs(df[[col, target_col]].corr().iloc[0, 1])
                if corr > 0.95:
                    razones.append(f"correlacion_extrema: {corr:.3f}")
                elif corr > 0.85:
                    razones.append(f"correlacion_muy_alta: {corr:.3f}")
            except Exception:
                pass

        # 3. Variables que separan perfectamente las clases
        if row["rol"] == "flag" and col in df.columns:
            try:
                if df.groupby(col)[target_col].mean().nunique() <= 2:
                    means = df.groupby(col)[target_col].mean()
                    if means.max() > 0.95 or means.min() < 0.05:
                        if abs(means.max() - means.min()) > 0.8:
                            razones.append("separacion_casi_perfecta")
            except Exception:
                pass

        if razones:
            sospechosas.append({"variable": col, "razones": "; ".join(razones)})

    return pd.DataFrame(sospechosas)

leakage_report = detectar_leakage(df, TARGET_COL, col_info)
if len(leakage_report) > 0:
    print(f"\n⚠️ {len(leakage_report)} variables sospechosas de LEAKAGE:")
    print(leakage_report.to_string(index=False))
    leakage_report.to_csv(PROJECT_ROOT / "reports" / "leakage_sospechosas.csv", index=False)
else:
    print("✅ No se detectaron variables sospechosas de leakage automáticamente")

# ACCION OBLIGATORIA:
# 1. Revisar variables sospechosas, columnas post-evento y restricciones del caso.
# 2. Agregar a LEAKAGE_COLS solo las fugas confirmadas.
# 3. Documentar cada decision y marcar LEAKAGE_REVIEW_DONE=True.
leakage_review = leakage_report.copy()
if leakage_review.empty:
    leakage_review = pd.DataFrame(columns=["variable", "razones"])
leakage_review["decision"] = "pendiente"   # eliminar_fuga | mantener | pendiente
leakage_review["justificacion_revision"] = ""
leakage_review.to_csv(PROJECT_ROOT / "reports" / "leakage_review.csv", index=False)

# Ejemplo despues de revisar:
# LEAKAGE_COLS += ["FECHA_BAJA", "MOTIVO_BAJA"]
# LEAKAGE_REVIEW_DONE = True
```

### B.4 Separar columnas por rol

```python
# Obtener listas de columnas por rol
DROP_COLS = ID_COLS + LEAKAGE_COLS + [TARGET_COL]
drop_roles = {"target", "id", "leakage", "constante", "posible_id", "fecha", "fecha_probable"}

num_cols = col_info[
    (col_info["rol"].isin(["numerica", "flag"])) &
    (~col_info["variable"].isin(DROP_COLS))
]["variable"].tolist()

cat_cols = col_info[
    (col_info["rol"] == "categorica") &
    (~col_info["variable"].isin(DROP_COLS))
]["variable"].tolist()

flag_cols = col_info[
    (col_info["rol"] == "flag") &
    (~col_info["variable"].isin(DROP_COLS))
]["variable"].tolist()

print(f"Numéricas: {len(num_cols)} | Categóricas: {len(cat_cols)} | Flags: {len(flag_cols)}")
print(f"A eliminar: {len(DROP_COLS)} ({DROP_COLS})")

# Ninguna familia temporal usada en features puede consumir fuga confirmada.
familias = {
    pref: [col for col in cols if col not in LEAKAGE_COLS]
    for pref, cols in familias.items()
}
familias = {pref: cols for pref, cols in familias.items() if len(cols) >= 3}

review_actual = pd.read_csv(PROJECT_ROOT / "reports" / "leakage_review.csv")
sin_pendientes = review_actual.empty or not review_actual["decision"].eq("pendiente").any()

GATE_CONDITIONS["target_definido"] = True
GATE_CONDITIONS["leakage_revisado"] = bool(LEAKAGE_REVIEW_DONE and sin_pendientes)
```

### B.5 Checkpoint Fase B

```python
assert GATE_CONDITIONS["target_definido"], "❌ Target no definido"
assert GATE_CONDITIONS["leakage_revisado"], "❌ Leakage no revisado/documentado"
print("✅ Fase B completada — Target y leakage analizados")
```

---

## FASE C — Análisis Univariado y Bivariado

### C.1 Diccionario automático de variables

```python
def crear_diccionario_completo(df, target_col, num_cols, cat_cols):
    """Genera diccionario enriquecido con estadísticas y relación con target."""
    registros = []

    for col in df.columns:
        if col == target_col:
            continue
        r = {
            "variable": col,
            "dtype": str(df[col].dtype),
            "n_nulos": int(df[col].isna().sum()),
            "pct_nulos": round(df[col].isna().mean() * 100, 2),
            "n_unicos": int(df[col].nunique(dropna=False)),
        }

        if col in num_cols:
            r["tipo"] = "numerica"
            r["media"] = round(df[col].mean(), 4) if df[col].notna().any() else None
            r["mediana"] = round(df[col].median(), 4) if df[col].notna().any() else None
            r["std"] = round(df[col].std(), 4) if df[col].notna().any() else None
            r["min"] = df[col].min() if df[col].notna().any() else None
            r["max"] = df[col].max() if df[col].notna().any() else None
            r["skew"] = round(df[col].skew(), 3) if df[col].notna().any() else None
            r["kurtosis"] = round(df[col].kurtosis(), 3) if df[col].notna().any() else None
            try:
                r["corr_target"] = round(df[[col, target_col]].corr().iloc[0, 1], 4)
            except Exception:
                r["corr_target"] = None
        elif col in cat_cols:
            r["tipo"] = "categorica"
            r["top_categoria"] = str(df[col].mode().iloc[0]) if df[col].notna().any() else None
            r["top_freq_pct"] = round(df[col].value_counts(normalize=True).iloc[0] * 100, 2) if df[col].notna().any() else None
        else:
            r["tipo"] = "otro"

        registros.append(r)

    return pd.DataFrame(registros).sort_values("pct_nulos", ascending=False)

diccionario = crear_diccionario_completo(df, TARGET_COL, num_cols, cat_cols)
diccionario.to_csv(PROJECT_ROOT / "reports" / "feature_dictionary.csv", index=False)
print(f"📖 Diccionario generado: {len(diccionario)} variables")
```

### C.2 Reporte de nulos — Decisiones

```python
def reporte_nulos_con_decision(df, target_col):
    """Genera reporte de nulos con decisión sugerida por umbral."""
    missing = pd.DataFrame({
        "variable": df.columns,
        "n_nulos": df.isna().sum().values,
        "pct_nulos": (df.isna().mean() * 100).round(2).values,
    }).sort_values("pct_nulos", ascending=False)

    def decision_nulos(pct):
        if pct == 0:
            return "mantener"
        elif pct <= 5:
            return "imputar_simple"
        elif pct <= 10:
            return "imputar_documentar"
        elif pct <= 35:
            return "imputar_con_indicador"
        elif pct <= 70:
            return "evaluar_eliminar_o_binaria"
        else:
            return "eliminar_o_binaria_presencia"

    missing["decision_sugerida"] = missing["pct_nulos"].apply(decision_nulos)
    return missing[missing["pct_nulos"] > 0]

nulos_report = reporte_nulos_con_decision(df, TARGET_COL)
print(nulos_report.head(20).to_string(index=False))

# Gráfico de nulos
cols_con_nulos = nulos_report[nulos_report["pct_nulos"] > 0].head(30)
if len(cols_con_nulos) > 0:
    fig, ax = plt.subplots(figsize=(10, max(6, len(cols_con_nulos) * 0.35)))
    colors = [PALETTE["pos"] if p > 35 else PALETTE["neg"] for p in cols_con_nulos["pct_nulos"]]
    ax.barh(cols_con_nulos["variable"], cols_con_nulos["pct_nulos"], color=colors)
    ax.set_xlabel("% Nulos")
    ax.set_title("Variables con Valores Faltantes", fontsize=14, fontweight="bold")
    ax.axvline(x=35, color="red", linestyle="--", alpha=0.5, label="Umbral 35%")
    ax.legend()
    ax.invert_yaxis()
    save_fig("missing_values_barplot")
```

**Tabla de decisión para nulos:**

| % Nulos | Acción | Justificación |
|---:|---|---|
| 0% | Mantener | Sin tratamiento necesario |
| 0–5% | Imputación simple | Mediana (num) o moda (cat) |
| 5–10% | Imputar y documentar | Evaluar si patrón de nulo es informativo |
| 10–35% | Imputar + crear indicador `_missing` | El nulo puede ser señal predictiva |
| 35–70% | Evaluar eliminar o crear binaria de presencia | Costo/beneficio de mantener |
| >70% | Eliminar o solo indicador de presencia | Imputar introduce demasiado ruido |

### C.3 Análisis de duplicados

```python
dup_filas = df.duplicated().sum()
print(f"Duplicados exactos: {dup_filas} ({dup_filas/len(df)*100:.2f}%)")

for id_col in ID_COLS:
    if id_col in df.columns:
        dup_id = df[id_col].duplicated().sum()
        print(f"Duplicados por {id_col}: {dup_id}")
        if dup_id > 0:
            print(f"  ⚠️ Hay {dup_id} IDs duplicados. Verificar si es multi-periodo o error.")
```

### C.4 Análisis univariado — Numéricas

```python
def analisis_univariado_numerico(df, num_cols, max_cols=50):
    """Estadísticas descriptivas extendidas para variables numéricas."""
    cols_usar = num_cols[:max_cols]
    stats = df[cols_usar].describe(percentiles=[0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]).T
    stats["skew"] = df[cols_usar].skew()
    stats["kurtosis"] = df[cols_usar].kurtosis()
    stats["pct_zeros"] = (df[cols_usar] == 0).mean() * 100

    # Flags de alerta
    stats["alerta"] = ""
    stats.loc[stats["std"] < 0.001, "alerta"] += "casi_constante; "
    stats.loc[abs(stats["skew"]) > 3, "alerta"] += "muy_asimetrica; "
    stats.loc[stats["kurtosis"] > 10, "alerta"] += "cola_pesada; "
    stats.loc[stats["pct_zeros"] > 90, "alerta"] += ">90%_ceros; "

    return stats.round(4)

stats_num = analisis_univariado_numerico(df, num_cols)
print(stats_num[stats_num["alerta"] != ""][["mean", "std", "skew", "alerta"]])
```

### C.5 Análisis univariado — Categóricas

```python
def analisis_univariado_categorico(df, cat_cols, max_cats_show=10):
    """Resumen de variables categóricas con alertas."""
    resultados = []
    for col in cat_cols:
        vc = df[col].value_counts(dropna=False)
        top_pct = vc.iloc[0] / len(df) * 100
        n_raras = (vc / len(df) < 0.01).sum()

        alerta = ""
        if top_pct > 95:
            alerta = "dominante_>95%"
        elif df[col].nunique() > 50:
            alerta = "alta_cardinalidad"
        elif n_raras > df[col].nunique() * 0.5:
            alerta = "muchas_raras"

        resultados.append({
            "variable": col,
            "n_categorias": df[col].nunique(dropna=False),
            "top_valor": str(vc.index[0]),
            "top_pct": round(top_pct, 2),
            "n_raras": n_raras,
            "alerta": alerta,
        })

    return pd.DataFrame(resultados).sort_values("n_categorias", ascending=False)

stats_cat = analisis_univariado_categorico(df, cat_cols)
print(stats_cat.to_string(index=False))
```

### C.6 Bivariado — Numéricas vs Target (ANOVA + Mutual Information)

```python
from sklearn.feature_selection import f_classif, mutual_info_classif

def bivariado_numerico_vs_target(df, num_cols, target_col, random_state=42):
    """
    ANOVA F-test + Mutual Information para variables numéricas vs target categórico.
    """
    # Preparar datos (imputación temporal con mediana solo para el test)
    X_num = df[num_cols].copy()
    X_num = X_num.fillna(X_num.median())
    y = df[target_col]

    # Filtrar filas con target no nulo
    mask = y.notna()
    X_num = X_num[mask]
    y = y[mask]

    # ANOVA
    f_values, p_values = f_classif(X_num, y)
    anova = pd.DataFrame({
        "variable": num_cols,
        "f_value": f_values,
        "p_value": p_values,
    })

    # Mutual Information
    mi_values = mutual_info_classif(X_num, y, random_state=random_state)
    anova["mutual_info"] = mi_values

    # Media por clase
    for cls in sorted(y.unique()):
        anova[f"media_clase_{cls}"] = X_num[y == cls].mean().values

    anova = anova.sort_values("f_value", ascending=False)
    anova["rank_anova"] = range(1, len(anova) + 1)
    anova["rank_mi"] = anova["mutual_info"].rank(ascending=False).astype(int)

    return anova

if TIPO_PROBLEMA in ("clasificacion_binaria", "multiclase"):
    biv_num = bivariado_numerico_vs_target(df, num_cols, TARGET_COL, RANDOM_STATE)
    print("\n📊 Top 20 variables numéricas por F-value:")
    print(biv_num.head(20)[["variable", "f_value", "p_value", "mutual_info", "rank_anova", "rank_mi"]].to_string(index=False))

    # Gráfico: Top 20 por Mutual Information
    top20_mi = biv_num.nlargest(20, "mutual_info")
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.barh(top20_mi["variable"], top20_mi["mutual_info"], color=PALETTE["pos"])
    ax.set_xlabel("Mutual Information")
    ax.set_title("Top 20 Variables — Mutual Information vs Target", fontsize=14, fontweight="bold")
    ax.invert_yaxis()
    save_fig("top20_mutual_information")
```

### C.7 Bivariado — Categóricas vs Target (Chi² + Cramér's V)

```python
from scipy.stats import chi2_contingency

def cramers_v(tabla_contingencia):
    """Calcula Cramér's V y p-value desde tabla de contingencia."""
    chi2, p, dof, expected = chi2_contingency(tabla_contingencia)
    n = tabla_contingencia.sum().sum()
    r, k = tabla_contingencia.shape
    v = np.sqrt((chi2 / n) / min(k - 1, r - 1)) if min(k - 1, r - 1) > 0 else 0
    return v, p

def bivariado_categorico_vs_target(df, cat_cols, target_col):
    """Chi-cuadrado + Cramér's V para categóricas vs target."""
    resultados = []
    for col in cat_cols:
        tabla = pd.crosstab(df[col], df[target_col])
        if tabla.shape[0] > 1 and tabla.shape[1] > 1:
            v, p = cramers_v(tabla)
            # Tasa del evento por categoría
            tasas = df.groupby(col)[target_col].mean()
            resultados.append({
                "variable": col,
                "cramers_v": round(v, 4),
                "p_value": p,
                "n_categorias": df[col].nunique(dropna=False),
                "tasa_min": round(tasas.min(), 4),
                "tasa_max": round(tasas.max(), 4),
                "rango_tasas": round(tasas.max() - tasas.min(), 4),
            })

    result = pd.DataFrame(resultados).sort_values("cramers_v", ascending=False)
    return result

if TIPO_PROBLEMA in ("clasificacion_binaria", "multiclase") and cat_cols:
    biv_cat = bivariado_categorico_vs_target(df, cat_cols, TARGET_COL)
    print("\n📊 Variables categóricas — Cramér's V:")
    print(biv_cat.to_string(index=False))
```

**Guía de interpretación — Cramér's V:**

| Cramér's V | Interpretación |
|---:|---|
| 0.00 – 0.10 | Asociación débil |
| 0.10 – 0.30 | Asociación moderada |
| 0.30 – 0.50 | Asociación fuerte |
| > 0.50 | Asociación muy fuerte — **verificar leakage** |

### C.8 Correlaciones y multicolinealidad

```python
def analizar_correlaciones(df, num_cols, umbral_alto=0.90, umbral_moderado=0.75):
    """Detecta pares de variables altamente correlacionadas."""
    corr = df[num_cols].corr(method="spearman")

    # Pares con alta correlación
    pares = []
    for i in range(len(corr.columns)):
        for j in range(i + 1, len(corr.columns)):
            r = corr.iloc[i, j]
            if abs(r) >= umbral_moderado:
                pares.append({
                    "var_1": corr.columns[i],
                    "var_2": corr.columns[j],
                    "spearman": round(r, 4),
                    "nivel": "MUY_ALTA" if abs(r) >= umbral_alto else "ALTA",
                })

    pares_df = pd.DataFrame(pares).sort_values("spearman", ascending=False, key=abs)

    # Heatmap si hay pocas variables
    if len(num_cols) <= 40:
        fig, ax = plt.subplots(figsize=(14, 12))
        sns.heatmap(corr, cmap="coolwarm", center=0, ax=ax,
                    xticklabels=True, yticklabels=True, fmt=".1f",
                    linewidths=0.5, linecolor=PALETTE["bg"],
                    cbar_kws={"shrink": 0.8})
        ax.set_title("Matriz de Correlación (Spearman)", fontsize=14, fontweight="bold")
        plt.xticks(fontsize=7, rotation=90)
        plt.yticks(fontsize=7)
        save_fig("correlation_heatmap")

    return pares_df

pares_correlacion = analizar_correlaciones(df, num_cols)
if len(pares_correlacion) > 0:
    print(f"\n⚠️ {len(pares_correlacion)} pares con correlación ≥ 0.75:")
    print(pares_correlacion.head(20).to_string(index=False))
    pares_correlacion.to_csv(PROJECT_ROOT / "reports" / "correlation_pairs.csv", index=False)
```

### C.9 VIF — Multicolinealidad (opcional, para datasets con pocas numéricas)

```python
def calcular_vif(df, num_cols, max_cols=30):
    """
    Calcula VIF. Solo aplicar si hay pocas columnas numéricas (<30).
    Para datasets grandes, usar correlación + importancia de modelo.
    """
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    import statsmodels.api as sm

    cols_usar = num_cols[:max_cols]
    X = df[cols_usar].dropna()

    if len(X) < 50 or len(cols_usar) < 2:
        print("⚠️ Datos insuficientes para VIF")
        return None

    X = sm.add_constant(X)
    vif = pd.DataFrame({
        "variable": X.columns,
        "VIF": [variance_inflation_factor(X.values, i) for i in range(X.shape[1])],
    })
    vif = vif[vif["variable"] != "const"].sort_values("VIF", ascending=False)

    return vif

# Solo ejecutar si hay pocas numéricas
if len(num_cols) <= 30:
    vif_data = calcular_vif(df, num_cols)
    if vif_data is not None:
        print("\n📊 VIF — Multicolinealidad:")
        print(vif_data[vif_data["VIF"] > 5].to_string(index=False))
```

**Guía VIF:**

| VIF | Interpretación |
|---:|---|
| 1 | Sin multicolinealidad |
| 1 – 5 | Aceptable |
| 5 – 10 | Revisar — posible redundancia |
| > 10 | Alta multicolinealidad — considerar eliminar una del par |

> Para modelos de boosting (LightGBM, XGBoost, CatBoost), la multicolinealidad no afecta el rendimiento pero puede afectar la interpretabilidad de importancias.

### C.10 Checkpoint Fase C

```python
print("✅ Fase C completada — Análisis univariado y bivariado")
```

---

## FASE D — Feature Engineering (Bancario)

> ⚠️ **PRINCIPIO**: Cada feature debe nacer de una pregunta de negocio. "¿El cliente está reduciendo su actividad?" → `trend_actividad`. No crear features arbitrarias.

### D.1 Features temporales para familias de columnas

```python
def crear_features_temporales(df, prefijo, columnas):
    """
    Crea features de agregación, tendencia y volatilidad
    para familias de columnas con sufijo temporal.

    Asume que columnas están ordenadas del periodo más reciente (_0)
    al más antiguo (_N).
    """
    fe = pd.DataFrame(index=df.index)
    vals = df[columnas].values  # array numpy para velocidad

    # --- Agregaciones básicas ---
    fe[f"{prefijo}_sum"] = np.nansum(vals, axis=1)
    fe[f"{prefijo}_mean"] = np.nanmean(vals, axis=1)
    fe[f"{prefijo}_max"] = np.nanmax(vals, axis=1)
    fe[f"{prefijo}_min"] = np.nanmin(vals, axis=1)
    fe[f"{prefijo}_std"] = np.nanstd(vals, axis=1)

    # --- Tendencia: periodo reciente vs antiguo ---
    n = len(columnas)
    mid = n // 2
    reciente = np.nansum(vals[:, :mid], axis=1)
    antiguo = np.nansum(vals[:, mid:], axis=1)
    fe[f"{prefijo}_trend"] = reciente - antiguo  # positivo = creciendo

    denominador = np.where(antiguo == 0, 1, antiguo)
    fe[f"{prefijo}_trend_pct"] = (reciente - antiguo) / denominador

    # --- Volatilidad (coeficiente de variación) ---
    mean_vals = np.nanmean(vals, axis=1)
    std_vals = np.nanstd(vals, axis=1)
    safe_mean = np.where(mean_vals == 0, 1, mean_vals)
    fe[f"{prefijo}_cv"] = std_vals / np.abs(safe_mean)

    # --- Meses en cero (inactividad) ---
    fe[f"{prefijo}_n_zeros"] = (vals == 0).sum(axis=1)
    fe[f"{prefijo}_pct_zeros"] = fe[f"{prefijo}_n_zeros"] / n

    # --- Último periodo vs promedio ---
    ultimo = df[columnas[0]].values
    fe[f"{prefijo}_ultimo_vs_media"] = ultimo - mean_vals

    # --- Decay: ¿cayó en últimos 2 periodos? ---
    if n >= 3:
        fe[f"{prefijo}_decay_2p"] = (
            df[columnas[0]].values < df[columnas[1]].values
        ).astype(int) & (
            df[columnas[1]].values < df[columnas[2]].values
        ).astype(int)

    # --- Máximo alcanzado vs último (pérdida desde pico) ---
    max_val = np.nanmax(vals, axis=1)
    safe_max = np.where(max_val == 0, 1, max_val)
    fe[f"{prefijo}_pct_desde_max"] = ultimo / safe_max

    return fe

# Aplicar a todas las familias detectadas
features_temporales = pd.DataFrame(index=df.index)
for prefijo, cols in familias.items():
    temp_fe = crear_features_temporales(df, prefijo, cols)
    features_temporales = pd.concat([features_temporales, temp_fe], axis=1)

print(f"✅ Features temporales creadas: {features_temporales.shape[1]}")
```

### D.2 Features cross-canal

```python
def crear_features_cross_canal(df, familias):
    """
    Crea features que combinan diferentes canales transaccionales.
    Detecta automáticamente familias tipo CANAL*.
    """
    fe = pd.DataFrame(index=df.index)

    # Identificar familias de canal
    canal_families = {k: v for k, v in familias.items() if "canal" in k.lower()}

    if not canal_families:
        print("  ℹ️ No se detectaron familias de canal")
        return fe

    # Actividad total por canal (suma de todos los periodos)
    canal_totales = {}
    for pref, cols in canal_families.items():
        canal_totales[pref] = df[cols].sum(axis=1)
        fe[f"{pref}_total"] = canal_totales[pref]

    # Actividad total global
    if canal_totales:
        total_global = sum(canal_totales.values())
        fe["actividad_total_canales"] = total_global

        # Concentración por canal (HHI simplificado)
        safe_total = total_global.replace(0, 1)
        for pref, total in canal_totales.items():
            fe[f"{pref}_share"] = total / safe_total

        # Canal dominante
        shares_df = pd.DataFrame(canal_totales)
        fe["canal_dominante"] = shares_df.idxmax(axis=1)
        fe["canal_dominante_pct"] = shares_df.max(axis=1) / safe_total

        # Diversificación (# canales con actividad > 0)
        fe["n_canales_activos"] = (shares_df > 0).sum(axis=1)

        # Ratio digital vs físico (requiere conocimiento del dominio)
        # Adaptar según nombres reales de canales digitales/físicos
        digital_keys = [k for k in canal_totales if any(d in k.lower() for d in ["internet", "app", "movil", "digital", "web"])]
        fisico_keys = [k for k in canal_totales if any(f in k.lower() for f in ["sucursal", "cajero", "atm", "ventanilla", "fisic"])]

        if digital_keys and fisico_keys:
            digital_total = sum(canal_totales[k] for k in digital_keys)
            fisico_total = sum(canal_totales[k] for k in fisico_keys)
            fe["ratio_digital_fisico"] = digital_total / (fisico_total + 1)
            fe["pct_digital"] = digital_total / (digital_total + fisico_total + 1)

    return fe

features_canal = crear_features_cross_canal(df, familias)
print(f"✅ Features cross-canal: {features_canal.shape[1]}")
```

### D.3 Features de engagement y riesgo

```python
def crear_features_engagement(df, familias, flag_cols, num_cols, features_canal_df=None):
    """Crea score de engagement compuesto y features de riesgo."""
    fe = pd.DataFrame(index=df.index)
    features_canal_df = features_canal_df if features_canal_df is not None else pd.DataFrame(index=df.index)

    # --- Flags activos (compromiso con productos) ---
    if flag_cols:
        fe["total_flags_activos"] = df[flag_cols].sum(axis=1)
        fe["pct_flags_activos"] = fe["total_flags_activos"] / max(len(flag_cols), 1)

    # --- Productos (si existe columna de número de productos) ---
    prod_cols = [c for c in df.columns if any(kw in c.lower() for kw in ["nro_prod", "num_prod", "n_producto", "productos"])]
    if prod_cols:
        fe["n_productos"] = df[prod_cols[0]]

    # --- Saldos (si existen columnas SDO) ---
    sdo_familias = {k: v for k, v in familias.items() if "sdo" in k.lower() or "saldo" in k.lower()}
    if sdo_familias:
        for pref, cols in sdo_familias.items():
            fe[f"{pref}_ultimo"] = df[cols[0]]
            fe[f"{pref}_promedio"] = df[cols].mean(axis=1)
            fe[f"{pref}_cambio"] = df[cols[0]] - df[cols[-1]]

    # --- Indicadores de riesgo de crédito avanzado (16+ features) ---
    
    # 1. Utilización de línea de crédito (Apalancamiento)
    if "saldo_deudor_total" in df.columns and "linea_credito_total" in df.columns:
        safe_line = np.where(df["linea_credito_total"] <= 0, 1, df["linea_credito_total"])
        fe["utilizacion_linea"] = df["saldo_deudor_total"] / safe_line
        
        # 2. Flag de sobregiro (saldo supera la línea de crédito aprobada)
        fe["flag_sobregiro"] = (df["saldo_deudor_total"] > df["linea_credito_total"]).astype(int)

    # 3. Ratio deuda-ingreso (Apalancamiento vs. Capacidad)
    if "saldo_deudor_total" in df.columns and "ingreso_mensual" in df.columns:
        safe_income = np.where(df["ingreso_mensual"].isna() | (df["ingreso_mensual"] <= 0), 1025, df["ingreso_mensual"])
        fe["ratio_deuda_ingreso"] = df["saldo_deudor_total"] / safe_income

    # 4. Capacidad de pago neta (Margen disponible libre de deuda)
    if "ingreso_mensual" in df.columns and "saldo_deudor_total" in df.columns:
        fe["capacidad_pago_neta"] = df["ingreso_mensual"].fillna(1025) - df["saldo_deudor_total"]

    # 5. Buró - Flag sin historial crediticio (Tratamiento estratégico del nulo en score_buro)
    if "score_buro" in df.columns:
        fe["buro_sin_historial"] = df["score_buro"].isna().astype(int)
        
        # 6. Buró - Flag con historial crediticio
        fe["buro_con_historial"] = df["score_buro"].notna().astype(int)
        
        # 7. Buró - Score corregido (Imputación neutra en base a nulo de historial)
        fe["score_buro_corregido"] = df["score_buro"].fillna(300) # 300 es el mínimo score posible
        
        # 8. Interacción Edad × Score Buró (Madurez financiera)
        if "edad" in df.columns:
            # Reemplazar edad negativa ruidosa (-999) por mediana típica de 40 años antes de interactuar
            edad_limpia = np.where((df["edad"] < 18) | (df["edad"] > 85), 40, df["edad"])
            fe["buro_score_risk"] = edad_limpia * fe["score_buro_corregido"]

    # 9. Días Mora Previa - Flag de ausencia de atrasos previos
    if "dias_mora_prev" in df.columns:
        fe["sin_mora_previa"] = df["dias_mora_prev"].isna().astype(int)
        
        # 10. Días Mora Previa - Máxima mora previa corregida
        fe["dias_mora_max_corregida"] = df["dias_mora_prev"].fillna(0)

        # 11. Interacción de Mora Previa y Buró (Severidad de atraso en base a historial externo)
        if "score_buro" in df.columns:
            fe["mora_score_interact"] = fe["dias_mora_max_corregida"] * (850 - fe["score_buro_corregido"])

    # 12. Atrasos del último año - Conteo total de atrasos en centrales
    atrasos_cols = [c for c in df.columns if any(kw in c.lower() for kw in ["atraso", "num_atraso"])]
    if atrasos_cols:
        fe["atrasos_totales"] = df[atrasos_cols].sum(axis=1)
        
        # 13. Conteo ponderado por gravedad del atraso
        p_cols = {
            "30_59": [c for c in atrasos_cols if "30" in c],
            "60_89": [c for c in atrasos_cols if "60" in c],
            "90_mas": [c for c in atrasos_cols if "90" in c]
        }
        ponderado = np.zeros(len(df))
        if p_cols["30_59"]:
            ponderado += 1.0 * df[p_cols["30_59"][0]]
        if p_cols["60_89"]:
            ponderado += 3.0 * df[p_cols["60_89"][0]]
        if p_cols["90_mas"]:
            ponderado += 10.0 * df[p_cols["90_mas"][0]]
        fe["atrasos_ponderados"] = ponderado
        
        # 14. Flag indicador de si alguna vez tuvo retrasos
        fe["tiene_atrasos_historicos"] = (fe["atrasos_totales"] > 0).astype(int)

    # 15. Frecuencia de Zona Geográfica (Frequency Encoding robusto contra leakage)
    if "zona_geografica" in df.columns:
        fe["zona_freq"] = df["zona_geografica"].map(df["zona_geografica"].value_counts(normalize=True))

    # 16. Frecuencia de Canal de Captación
    if "canal_captacion" in df.columns:
        fe["canal_freq"] = df["canal_captacion"].map(df["canal_captacion"].value_counts(normalize=True))

    # --- Rentabilidad y Score Compuesto Fila a Fila ---
    componentes = []
    if "buro_score_corregido" in fe.columns:
        componentes.append(0.5 * fe["score_buro_corregido"])
    if "capacidad_pago_neta" in fe.columns:
        componentes.append(0.01 * fe["capacidad_pago_neta"].clip(lower=0))
    if "atrasos_totales" in fe.columns:
        componentes.append(-50.0 * fe["atrasos_totales"])

    if componentes:
        fe["engagement_score_raw"] = sum(componentes)

    return fe

features_engagement = crear_features_engagement(
    df, familias, flag_cols, num_cols, features_canal_df=features_canal
)
print(f"✅ Features engagement/riesgo bancario: {features_engagement.shape[1]}")
```

### D.4 Features de missing como señal

```python
def crear_features_missing(df, columnas_missing, excluir_cols=None):
    """
    Crea indicadores binarios para columnas de missing aprobadas por el EDA.
    En banca, el patrón de missing puede ser muy predictivo
    (ej: cliente sin datos de nómina → no tiene nómina).
    """
    fe = pd.DataFrame(index=df.index)
    excluir_cols = set(excluir_cols or [])
    cols_base = [c for c in df.columns if c not in excluir_cols]
    cols_con_nulos = [c for c in columnas_missing if c in cols_base]

    for col in cols_con_nulos:
        fe[f"flg_null_{col}"] = df[col].isna().astype(int)

    # Score de completitud (% de campos rellenos por cliente)
    fe["pct_campos_completos"] = (1 - df[cols_base].isna().mean(axis=1)) * 100
    fe["n_campos_nulos"] = df[cols_base].isna().sum(axis=1)

    print(f"  Indicadores de missing creados: {len(cols_con_nulos)}")
    return fe

missing_cols_signal = nulos_report[nulos_report["pct_nulos"] > 10]["variable"].tolist()
features_missing = crear_features_missing(
    df,
    columnas_missing=missing_cols_signal,
    excluir_cols=ID_COLS + LEAKAGE_COLS + [TARGET_COL],
)
print(f"✅ Features missing: {features_missing.shape[1]}")
```

### D.5 Features de recencia

```python
def crear_features_recencia(df, familias):
    """
    Para familias temporales, calcula cuántos periodos han pasado
    desde la última actividad (> 0).
    """
    fe = pd.DataFrame(index=df.index)

    for prefijo, cols in familias.items():
        # cols[0] = más reciente, cols[-1] = más antiguo
        vals = df[cols].values
        recencia = np.full(len(df), len(cols))  # default = nunca tuvo actividad
        for i in range(len(cols)):
            mask = vals[:, i] > 0
            recencia[mask] = np.minimum(recencia[mask], i)
        fe[f"{prefijo}_recencia"] = recencia

    return fe

features_recencia = crear_features_recencia(df, familias)
print(f"✅ Features recencia: {features_recencia.shape[1]}")
```

### D.6 Consolidar todas las features

```python
def consolidar_features(df_original, *feature_dfs, target_col, id_cols, drop_cols):
    """
    Consolida el dataframe original con todas las features creadas.
    Elimina columnas originales innecesarias. Mantiene target e IDs.
    """
    df_fe = df_original.copy()

    for fe_df in feature_dfs:
        # Evitar duplicados de columnas
        new_cols = [c for c in fe_df.columns if c not in df_fe.columns]
        if new_cols:
            df_fe = pd.concat([df_fe, fe_df[new_cols]], axis=1)

    # Eliminar leakage y constantes
    cols_eliminar = [c for c in drop_cols if c in df_fe.columns and c != target_col]
    df_fe.drop(columns=cols_eliminar, errors="ignore", inplace=True)

    # Eliminar constantes generadas
    const_cols = [c for c in df_fe.columns if df_fe[c].nunique() <= 1 and c != target_col]
    if const_cols:
        print(f"  Eliminando {len(const_cols)} constantes generadas: {const_cols[:5]}...")
        df_fe.drop(columns=const_cols, inplace=True)

    n_originales = len(df_original.columns)
    n_final = len(df_fe.columns)
    n_nuevas = n_final - n_originales + len(cols_eliminar)
    print(f"\n📦 Consolidación:")
    print(f"  Originales: {n_originales} | Eliminadas: {len(cols_eliminar)} | Nuevas: {n_nuevas} | Total: {n_final}")

    return df_fe

df_fe = consolidar_features(
    df,
    features_temporales,
    features_canal,
    features_engagement,
    features_missing,
    features_recencia,
    target_col=TARGET_COL,
    id_cols=ID_COLS,
    drop_cols=LEAKAGE_COLS,
)

GATE_CONDITIONS["features_creadas"] = True
```

**Contrato de reproducibilidad:** las funciones que producen `features_temporales`, `features_canal`, `features_engagement`, `features_missing` y `features_recencia` deben poder ejecutarse sobre train y sobre un test sin target. Si existe submission, moverlas a `src/feature_builder.py` con una entrada raw, listas fijas como `missing_cols_signal` y una salida con las mismas columnas de features; no dejar esa logica solo dentro de una celda del EDA.

### D.7 Checkpoint Fase D

```python
assert GATE_CONDITIONS["features_creadas"], "❌ Features no creadas"
assert df_fe.shape[1] > df.shape[1], "❌ No se crearon features nuevas"
print(f"✅ Fase D completada — {df_fe.shape[1]} columnas totales")
```

---

## FASE E — Selección y Ranking de Features

### E.1 Ranking unificado de features

Este ranking es exploratorio y sirve para revisar senal, redundancia y posibles fugas. No reemplaza la comparacion de modelos ni una seleccion validada despues del split en el Doc 2.

```python
def ranking_unificado_features(df, target_col, id_cols, random_state=42):
    """
    Genera ranking unificado combinando ANOVA, Mutual Information
    y correlación. Solo para clasificación.
    """
    drop = id_cols + [target_col]
    num_cols_fe = [c for c in df.select_dtypes(include=[np.number]).columns if c not in drop]

    X = df[num_cols_fe].copy()
    y = df[target_col].copy()

    # Filtrar NaN en target
    mask = y.notna()
    X = X[mask]
    y = y[mask]

    # Imputar con mediana (temporal, solo para ranking)
    X = X.fillna(X.median())

    # ANOVA
    f_vals, p_vals = f_classif(X, y)

    # Mutual Information
    mi_vals = mutual_info_classif(X, y, random_state=random_state)

    # Correlación absoluta con target
    corr_vals = X.corrwith(y).abs().values

    ranking = pd.DataFrame({
        "variable": num_cols_fe,
        "f_value": f_vals,
        "p_value": p_vals,
        "mutual_info": mi_vals,
        "abs_corr": corr_vals,
        "pct_nulos": df[num_cols_fe].isna().mean().values * 100,
    })

    # Ranks individuales
    ranking["rank_f"] = ranking["f_value"].rank(ascending=False)
    ranking["rank_mi"] = ranking["mutual_info"].rank(ascending=False)
    ranking["rank_corr"] = ranking["abs_corr"].rank(ascending=False)

    # Score combinado (promedio de ranks — menor es mejor)
    ranking["rank_promedio"] = (ranking["rank_f"] + ranking["rank_mi"] + ranking["rank_corr"]) / 3
    ranking = ranking.sort_values("rank_promedio")
    ranking["rank_final"] = range(1, len(ranking) + 1)

    # Señalar posible leakage
    ranking["alerta_leakage"] = ""
    ranking.loc[ranking["abs_corr"] > 0.9, "alerta_leakage"] = "⚠️ POSIBLE LEAKAGE"
    ranking.loc[(ranking["mutual_info"] > ranking["mutual_info"].quantile(0.99)) &
                (ranking["abs_corr"] > 0.8), "alerta_leakage"] = "⚠️ POSIBLE LEAKAGE"

    return ranking

if TIPO_PROBLEMA in ("clasificacion_binaria", "multiclase"):
    feature_ranking = ranking_unificado_features(df_fe, TARGET_COL, ID_COLS, RANDOM_STATE)
    feature_ranking.to_csv(PROJECT_ROOT / "reports" / "feature_ranking.csv", index=False)

    print("\n🏆 Top 30 features por ranking unificado:")
    cols_show = ["rank_final", "variable", "f_value", "mutual_info", "abs_corr", "pct_nulos", "alerta_leakage"]
    print(feature_ranking.head(30)[cols_show].to_string(index=False))

    # Alertas de leakage
    alertas = feature_ranking[feature_ranking["alerta_leakage"] != ""]
    if len(alertas) > 0:
        print(f"\n⚠️ {len(alertas)} variables con alerta de leakage:")
        print(alertas[["variable", "abs_corr", "mutual_info", "alerta_leakage"]].to_string(index=False))

    # Gráfico Top 30
    top30 = feature_ranking.head(30)
    fig, ax = plt.subplots(figsize=(10, 10))
    colors = [PALETTE["pos"] if a == "" else "red" for a in top30["alerta_leakage"]]
    ax.barh(top30["variable"], top30["mutual_info"], color=colors)
    ax.set_xlabel("Mutual Information")
    ax.set_title("Top 30 Features — Ranking Unificado", fontsize=14, fontweight="bold")
    ax.invert_yaxis()
    save_fig("feature_ranking_top30")

GATE_CONDITIONS["feature_ranking_listo"] = True
```

### E.2 Decisión de variables — Matriz final

```python
def generar_matriz_decision(col_info, feature_ranking, nulos_report, pares_correlacion, leakage_cols):
    """
    Genera matriz final con decisión por variable:
    mantener, eliminar_fuga, eliminar_nulos, eliminar_varianza, transformar, revisar.
    """
    decisiones = []

    for _, row in col_info.iterrows():
        var = row["variable"]
        decision = "mantener"
        justificacion = []

        # Fuga
        if var in leakage_cols or row["rol"] in ("leakage", "id", "constante", "posible_id"):
            decision = f"eliminar_{row['rol']}"
            justificacion.append(row["rol"])

        # Nulos excesivos
        elif row["pct_nulos"] > 95:
            decision = "eliminar_nulos_extremos"
            justificacion.append(f"{row['pct_nulos']}% nulos")

        # Target
        elif row["rol"] == "target":
            decision = "target"
            justificacion.append("variable objetivo")

        # Fechas
        elif row["rol"] in ("fecha", "fecha_probable"):
            decision = "transformar_o_eliminar"
            justificacion.append("variable de fecha")

        else:
            # Verificar ranking si existe
            if feature_ranking is not None and var in feature_ranking["variable"].values:
                rank_row = feature_ranking[feature_ranking["variable"] == var].iloc[0]
                if rank_row.get("alerta_leakage", "") != "":
                    decision = "revisar_leakage"
                    justificacion.append("alerta leakage en ranking")

            justificacion.append(f"nulos: {row['pct_nulos']}%")

        decisiones.append({
            "variable": var,
            "rol": row["rol"],
            "pct_nulos": row["pct_nulos"],
            "decision": decision,
            "justificacion": "; ".join(justificacion),
        })

    return pd.DataFrame(decisiones)

fr = feature_ranking if "feature_ranking" in dir() else None
matriz_decision = generar_matriz_decision(col_info, fr, nulos_report, pares_correlacion, LEAKAGE_COLS)
print(f"\n📋 Decisiones por variable:")
print(matriz_decision["decision"].value_counts())
matriz_decision.to_csv(PROJECT_ROOT / "reports" / "variable_decisions.csv", index=False)
```

### E.3 Checkpoint Fase E

```python
assert GATE_CONDITIONS["feature_ranking_listo"], "❌ Feature ranking no completado"
print("✅ Fase E completada — Ranking y decisiones de variables")
```

---

## FASE F — Preparacion para el Pipeline de Modelado

Esta fase deja decisiones y columnas listas para el Doc 2. No se ajusta un preprocessor con todo el dataset: imputacion, categorias raras aprendidas por frecuencia, escalado y cuantiles de outliers se aprenden despues del split usando train.

### F.1 Politica de outliers para Doc 2

```python
def winsorizar_columnas(df, columnas, p_low=0.01, p_high=0.99):
    """Plantilla para un transformer que debe ajustar cuantiles solo con train."""
    df_w = df.copy()
    registro = []
    for col in columnas:
        if col in df_w.columns and df_w[col].dtype in ("float64", "int64", "float32", "int32"):
            low = df_w[col].quantile(p_low)
            high = df_w[col].quantile(p_high)
            n_afectados = ((df_w[col] < low) | (df_w[col] > high)).sum()
            if n_afectados > 0:
                df_w[col] = df_w[col].clip(lower=low, upper=high)
                registro.append({"variable": col, "low": low, "high": high, "n_afectados": n_afectados})
    if registro:
        print(f"  Winsorización aplicada a {len(registro)} variables")
    return df_w, pd.DataFrame(registro)
```

**Tabla de decisión para outliers:**

| Tipo de outlier | Acción | Ejemplo bancario |
|---|---|---|
| Error evidente (edad = 999) | Corregir o imputar | Dato de captura erróneo |
| Cliente premium | Mantener | Saldo muy alto, legítimo |
| Transacción sospechosa | Mantener + crear flag | Monto atípico |
| Valor extremo que distorsiona | Winsorizar p01-p99 | Cola larga en montos |
| Variable monetaria con sesgo fuerte | `np.log1p()` | Ingresos, montos |

### F.2 Politica de categoricas

La limpieza deterministica de texto puede vivir en `src/feature_builder.py`. El agrupamiento de categorias raras por frecuencia debe implementarse como transformacion ajustada en train dentro del pipeline del Doc 2.

```python
def limpiar_texto_categoricas(df, cat_cols):
    """Normaliza texto sin aprender frecuencias del dataset."""
    df_prep = df.copy()
    for col in cat_cols:
        if col in df_prep.columns and df_prep[col].dtype == "object":
            # Normalizar texto
            df_prep[col] = (
                df_prep[col]
                .astype(str)
                .str.strip()
                .str.lower()
                .str.normalize("NFKD")
                .str.encode("ascii", errors="ignore")
                .str.decode("utf-8")
            )
            # Reemplazar "nan" literal
            df_prep[col] = df_prep[col].replace("nan", np.nan)

    return df_prep
```

### F.3 Transformaciones logaritmicas

Aplicar `log1p` aqui solo cuando la regla venga del dominio y quede reutilizable para train/test. Si la decision depende de skewness, cuantiles o validacion, moverla al Doc 2.

```python
def aplicar_log_transform(df, columnas):
    """
    Aplica log1p a columnas aprobadas por regla de dominio.
    No decide columnas por skewness calculado sobre todo el dataset.
    """
    df_t = df.copy()
    transformadas = []
    for col in columnas:
        if col in df_t.columns:
            min_val = df_t[col].min()
            if min_val >= 0:
                df_t[f"{col}_log"] = np.log1p(df_t[col])
                transformadas.append({"variable": col, "transformacion": "log1p"})
    if transformadas:
        print(f"  Log-transform aplicado a {len(transformadas)} variables")
    return df_t, pd.DataFrame(transformadas)
```

### F.4 Contrato del pipeline sklearn

Este bloque describe la forma esperada del pipeline. El `fit`, la serializacion y cualquier transformer que aprenda estadisticas pertenecen al Doc 2.

```python
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler, OrdinalEncoder
from sklearn.impute import SimpleImputer

def construir_pipeline(num_cols_final, cat_cols_final, escalar=True):
    """
    Construye pipeline de preprocesamiento.
    IMPORTANTE: Ajustar SOLO con datos de train.
    """
    pasos_num = [("imputer_num", SimpleImputer(strategy="median"))]
    if escalar:
        pasos_num.append(("scaler", RobustScaler()))

    num_pipeline = Pipeline(steps=pasos_num)

    cat_pipeline = Pipeline(steps=[
        ("imputer_cat", SimpleImputer(strategy="constant", fill_value="desconocido")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False, max_categories=20)),
    ])

    transformers = [("num", num_pipeline, num_cols_final)]
    if cat_cols_final:
        transformers.append(("cat", cat_pipeline, cat_cols_final))

    preprocessor = ColumnTransformer(
        transformers=transformers,
        remainder="drop",
    )

    return preprocessor

# Definir columnas finales
cols_mantener = matriz_decision[matriz_decision["decision"] == "mantener"]["variable"].tolist()
num_cols_final = [c for c in cols_mantener if c in df_fe.select_dtypes(include=[np.number]).columns]
cat_cols_final = [c for c in cols_mantener if c in df_fe.select_dtypes(include=["object", "category"]).columns]

# No escalar si se usarán modelos de boosting (más común en datathon)
preprocessor = construir_pipeline(num_cols_final, cat_cols_final, escalar=False)
print(f"Pipeline: {len(num_cols_final)} numéricas + {len(cat_cols_final)} categóricas")
```

### F.5 Dataset de modelado sin fit global

```python
def preparar_dataset_modelado(df_features, matriz_decision, target_col, id_cols,
                              leakage_cols, raw_columns):
    """
    Exporta el contrato de features para Doc 2 sin imputar sobre todo el dataset.
    Conserva IDs necesarios para split/submission y mantiene nulos para que el
    preprocessor del Doc 2 aprenda estadisticas solo desde train.
    """
    raw_keep = matriz_decision[
        matriz_decision["decision"].eq("mantener")
    ]["variable"].tolist()

    engineered_cols = [
        c for c in df_features.columns
        if c not in raw_columns and c not in id_cols + [target_col]
    ]
    feature_cols = [
        c for c in raw_keep + engineered_cols
        if c in df_features.columns and c not in leakage_cols + id_cols + [target_col]
    ]
    feature_cols = list(dict.fromkeys(feature_cols))

    export_cols = [c for c in id_cols if c in df_features.columns]
    export_cols += feature_cols
    export_cols += [target_col]
    return df_features[export_cols].copy(), feature_cols

df_procesado, feature_cols_modelado = preparar_dataset_modelado(
    df_fe,
    matriz_decision,
    TARGET_COL,
    ID_COLS,
    LEAKAGE_COLS,
    raw_columns=df.columns.tolist(),
)

# El gate significa "politica de nulos documentada", no "imputacion global aplicada".
GATE_CONDITIONS["nulos_tratados"] = bool(
    nulos_report.empty or "decision_sugerida" in nulos_report.columns
)
```

### F.6 Checkpoint Fase F

```python
assert GATE_CONDITIONS["nulos_tratados"], "❌ Falta politica documentada para nulos"
assert TARGET_COL in df_procesado.columns, "❌ El dataset exportable perdio el target"
assert not set(LEAKAGE_COLS).intersection(feature_cols_modelado), "❌ Hay fuga confirmada en features"
print("✅ Fase F completada — Features listas para split; preprocesamiento se ajusta en Doc 2")
```

---

## FASE G — Resumen EDA y Handoff al Modelado

### G.1 Exportar datasets procesados

```python
def exportar_datasets(df_original, df_procesado, target_col, id_cols, project_root):
    """Exporta features pre-split y una base de referencia para el modelado."""
    out_dir = project_root / "data" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Features pre-split; Doc 2 ajusta imputacion/encoding/escalado solo con train.
    df_procesado.to_parquet(out_dir / "features.parquet", index=False)
    print(f"  ✅ features.parquet: {df_procesado.shape}")

    # Base original de referencia (sin feature engineering)
    cols_original = [c for c in df_original.columns if c in df_procesado.columns or c == target_col]
    df_original[cols_original].to_parquet(out_dir / "base_original.parquet", index=False)
    print(f"  ✅ base_original.parquet: {df_original[cols_original].shape}")

    # Lista de features
    feature_list = [c for c in df_procesado.columns if c not in id_cols + [target_col]]
    with open(out_dir / "feature_list.txt", "w") as f:
        f.write("\n".join(feature_list))
    print(f"  ✅ feature_list.txt: {len(feature_list)} features")

    return feature_list

feature_list = exportar_datasets(df, df_procesado, TARGET_COL, ID_COLS, PROJECT_ROOT)
GATE_CONDITIONS["dataset_exportado"] = True
```

### G.2 Generar resumen EDA (eda_summary.csv)

```python
def generar_eda_summary(df_procesado, target_col, id_cols, feature_ranking=None):
    """Genera resumen por variable para referencia rápida."""
    drop = id_cols + [target_col]
    cols = [c for c in df_procesado.columns if c not in drop]

    resumen = []
    for col in cols:
        r = {
            "variable": col,
            "dtype": str(df_procesado[col].dtype),
            "null_pct": round(df_procesado[col].isna().mean() * 100, 2),
            "n_unicos": int(df_procesado[col].nunique()),
            "es_nueva": col not in df.columns,
        }
        if df_procesado[col].dtype in ("float64", "int64", "float32", "int32"):
            try:
                r["corr_target"] = round(df_procesado[[col, target_col]].corr().iloc[0, 1], 4)
            except Exception:
                r["corr_target"] = None
            r["media_pos"] = round(df_procesado[df_procesado[target_col] == 1][col].mean(), 4) \
                if TIPO_PROBLEMA == "clasificacion_binaria" else None
            r["media_neg"] = round(df_procesado[df_procesado[target_col] == 0][col].mean(), 4) \
                if TIPO_PROBLEMA == "clasificacion_binaria" else None

        if feature_ranking is not None and col in feature_ranking["variable"].values:
            rank_row = feature_ranking[feature_ranking["variable"] == col].iloc[0]
            r["rank_unificado"] = int(rank_row["rank_final"])
            r["mutual_info"] = round(rank_row["mutual_info"], 4)

        resumen.append(r)

    return pd.DataFrame(resumen).sort_values(
        "rank_unificado" if "rank_unificado" in pd.DataFrame(resumen).columns else "corr_target",
        ascending=True,
        na_position="last"
    )

eda_summary = generar_eda_summary(
    df_procesado, TARGET_COL, ID_COLS,
    feature_ranking if "feature_ranking" in dir() else None,
)
eda_summary.to_csv(PROJECT_ROOT / "reports" / "eda_summary.csv", index=False)
print(f"📊 EDA Summary: {len(eda_summary)} variables")
```

### G.3 Generar informe de handoff (JSON para el Orquestador)

```python
def generar_handoff(df_procesado, target_col, id_cols, target_info,
                    feature_list, gate_conditions, project_root):
    """
    Genera JSON de handoff con toda la información que necesita
    el Doc 2 (Modelado) para continuar.
    """
    handoff = {
        "status": "READY" if all(gate_conditions.values()) else "BLOCKED",
        "target_col": target_col,
        "id_cols": id_cols,
        "metrica_jurado": METRICA_JURADO,
        "tipo_problema": TIPO_PROBLEMA,
        "validation_strategy": VALIDATION_STRATEGY,
        "periodo_col": PERIODO_COL,
        "group_col": GROUP_COL,
        "feature_builder_path": str(FEATURE_BUILDER_PATH)
            if FEATURE_BUILDER_PATH.exists() else None,
        "features_pre_split": True,
        "gate_conditions": gate_conditions,
        "dataset": {
            "path": str(project_root / "data" / "processed" / "features.parquet"),
            "shape": list(df_procesado.shape),
            "n_features": len(feature_list),
            "feature_list_path": str(project_root / "data" / "processed" / "feature_list.txt"),
        },
        "target": {
            "nombre": target_col,
            "tipo_problema": TIPO_PROBLEMA,
            "metrica_jurado": METRICA_JURADO,
            "info": target_info,
        },
        "columnas": {
            "id_cols": id_cols,
            "target_col": target_col,
            "num_features": len([c for c in feature_list if df_procesado[c].dtype in ("float64", "int64")]),
            "cat_features": len([c for c in feature_list if df_procesado[c].dtype == "object"]),
        },
        "calidad": {
            "pct_nulos_max": round(df_procesado[feature_list].isna().mean().max() * 100, 2),
            "n_constantes": int((df_procesado[feature_list].nunique() <= 1).sum()),
        },
        "recomendaciones": {
            "escalar": TIPO_PROBLEMA != "clasificacion_binaria",  # boosting no necesita
            "balanceo": target_info.get("nivel", "") in ("SEVERO", "EXTREMO") if isinstance(target_info, dict) else False,
            "modelos_sugeridos": [
                "LightGBM", "XGBoost", "CatBoost", "RandomForest", "LogisticRegression"
            ],
        },
        "artefactos": {
            "eda_summary": str(project_root / "reports" / "eda_summary.csv"),
            "feature_dictionary": str(project_root / "reports" / "feature_dictionary.csv"),
            "feature_ranking": str(project_root / "reports" / "feature_ranking.csv"),
            "variable_decisions": str(project_root / "reports" / "variable_decisions.csv"),
            "leakage_review": str(project_root / "reports" / "leakage_review.csv"),
            "figures_dir": str(project_root / "reports" / "figures"),
        },
    }

    with open(project_root / "reports" / "eda_handoff.json", "w") as f:
        json.dump(handoff, f, indent=2, default=str)

    print(f"\n{'='*60}")
    print(f"📤 HANDOFF STATUS: {handoff['status']}")
    print(f"{'='*60}")
    print(f"  Dataset: {handoff['dataset']['shape']}")
    print(f"  Features: {handoff['dataset']['n_features']}")
    print(f"  Target: {target_col} ({TIPO_PROBLEMA})")
    print(f"  Métrica: {METRICA_JURADO}")
    print(f"  Balanceo recomendado: {handoff['recomendaciones']['balanceo']}")

    return handoff

pct_nulos_finales = df_procesado[feature_list].isna().mean() * 100
cols_nulos_extremos = pct_nulos_finales[pct_nulos_finales > 95].index.tolist()
GATE_CONDITIONS["calidad_aceptable"] = len(cols_nulos_extremos) == 0
if cols_nulos_extremos:
    print(f"⛔ Excluir o justificar features con >95% nulos: {cols_nulos_extremos}")

handoff = generar_handoff(
    df_procesado, TARGET_COL, ID_COLS, target_info,
    feature_list, GATE_CONDITIONS, PROJECT_ROOT,
)
```

### G.4 Resumen ejecutivo del EDA

```python
def imprimir_resumen_ejecutivo(df_original, df_procesado, target_col, target_info,
                               feature_list, familias, nulos_report):
    """Imprime resumen ejecutivo que documenta hallazgos clave."""
    print(f"""
{'='*70}
                    RESUMEN EJECUTIVO DEL EDA
{'='*70}

📊 DATOS ORIGINALES
  - Filas: {df_original.shape[0]:,}
  - Columnas originales: {df_original.shape[1]}

🎯 TARGET: {target_col}
  - Tipo de problema: {TIPO_PROBLEMA}
  - Info: {target_info}

📦 FEATURE ENGINEERING
  - Familias temporales detectadas: {len(familias)}
  - Features totales generadas: {len(feature_list)}
  - Features nuevas: {sum(1 for c in feature_list if c not in df_original.columns)}

🔍 CALIDAD
  - Columnas con >35% nulos: {len(nulos_report[nulos_report['pct_nulos'] > 35]) if nulos_report is not None else 'N/A'}
  - Columnas eliminadas por fuga: {len(LEAKAGE_COLS)}

📤 DATASET FINAL
  - Path: data/processed/features.parquet
  - Shape: {df_procesado.shape}
  - Métrica objetivo: {METRICA_JURADO}

{'='*70}
""")

imprimir_resumen_ejecutivo(df, df_procesado, TARGET_COL, target_info,
                           feature_list, familias, nulos_report)
```

### G.5 Verificación final del Gate

```python
gate_ok = verificar_gate()
if gate_ok:
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║  ✅ EDA COMPLETADO — LISTO PARA DOC 2 (MODELADO)       ║
    ║                                                          ║
    ║  Próximo paso: Abrir Modelado_Validacion_Datathon_Banca ║
    ║  y usar data/processed/features.parquet                  ║
    ║  con reports/eda_handoff.json como configuración          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
else:
    print("⛔ Revisar condiciones pendientes antes de continuar")
```

---

## CHECKLIST FINAL DEL EDA

Antes de cerrar el EDA y pasar al modelado, verificar:

### Datos
- [ ] Dataset cargado correctamente (formato detectado automáticamente)
- [ ] Etiquetas SPSS extraídas (si aplica)
- [ ] Variable objetivo identificada y confirmada
- [ ] IDs identificados y separados
- [ ] Duplicados revisados y documentados

### Calidad
- [ ] Tipos de datos corregidos
- [ ] Nulos analizados con decisión por columna
- [ ] Outliers detectados y tratamiento definido
- [ ] Rangos imposibles verificados
- [ ] Categóricas normalizadas (texto limpio)

### Anti-Leakage ⚠️
- [ ] Variables de fuga identificadas y removidas
- [ ] No hay variables post-evento en el dataset
- [ ] Correlaciones >0.9 con target revisadas manualmente
- [ ] Target encoding / WOE NO aplicado antes del split

### Análisis
- [ ] Distribución del target graficada y documentada
- [ ] Análisis bivariado completado (ANOVA + Chi² + MI)
- [ ] Correlaciones calculadas y pares redundantes documentados
- [ ] Top features identificadas por ranking unificado

### Feature Engineering
- [ ] Familias temporales detectadas y features creadas
- [ ] Features cross-canal generadas (si aplica)
- [ ] Engagement score construido
- [ ] Indicadores de missing creados
- [ ] Features de recencia generadas

### Exportación
- [ ] `data/processed/features.parquet` generado
- [ ] `data/processed/base_original.parquet` generado
- [ ] `reports/eda_summary.csv` guardado
- [ ] `reports/feature_dictionary.csv` guardado
- [ ] `reports/feature_ranking.csv` guardado
- [ ] `reports/leakage_review.csv` sin decisiones pendientes
- [ ] `reports/eda_handoff.json` generado
- [ ] `src/feature_builder.py` disponible si hay test/submission
- [ ] Figuras guardadas en `reports/figures/`
- [ ] Gate conditions verificadas

---

## ARTEFACTOS PRODUCIDOS

```text
project/
├── data/
│   ├── raw/                         # Datos originales (intactos)
│   └── processed/
│       ├── features.parquet         # Features pre-split para Doc 2
│       ├── base_original.parquet    # Base de referencia sin FE
│       └── feature_list.txt         # Lista de features entregadas
│
├── reports/
│   ├── eda_summary.csv              # Resumen estadístico por variable
│   ├── feature_dictionary.csv       # Diccionario completo de variables
│   ├── feature_ranking.csv          # Ranking unificado (ANOVA+MI+Corr)
│   ├── clasificacion_columnas.csv   # Roles de cada columna
│   ├── variable_decisions.csv       # Decisión por variable
│   ├── correlation_pairs.csv        # Pares altamente correlacionados
│   ├── data_quality_report.json     # Reporte de calidad
│   ├── leakage_sospechosas.csv      # Variables sospechosas de fuga
│   ├── leakage_review.csv           # Decision documentada sobre leakage
│   ├── etiquetas_spss.csv           # Etiquetas SPSS (si aplica)
│   ├── eda_handoff.json             # ★ Metadata para Doc 2
│   └── figures/
│       ├── target_distribution.png
│       ├── missing_values_barplot.png
│       ├── correlation_heatmap.png
│       ├── top20_mutual_information.png
│       └── feature_ranking_top30.png
│
├── src/
│   └── feature_builder.py           # Feature engineering reusable si hay submission
│
└── models/                          # Vacio; lo llena Doc 2
```

---

## NOTAS TÉCNICAS

### El p-value no basta

En datasets grandes (>10K filas), casi cualquier diferencia produce `p_value < 0.05`. Complementar siempre con:

- **Tamaño de efecto** (Cramér's V, diferencia de medias normalizada)
- **Mutual Information** (captura no linealidad)
- **Importancia en modelo** (validación cruzada con modelo baseline)
- **Estabilidad temporal** (si hay periodos)

### No todo outlier es error

En banca, los outliers son frecuentemente los casos más importantes:

| Caso | Ejemplo | Acción correcta |
|---|---|---|
| Fraude | Transacción 50x el promedio | Mantener |
| Cliente premium | Saldo >10M | Mantener |
| Error de captura | Edad = 999 | Corregir |
| Cola monetaria | Ingresos con sesgo fuerte | Winsorizar o log1p |

### Encoding después del split

**NUNCA** aplicar target encoding, WOE o IV sobre todo el dataset. Estos métodos usan la variable objetivo y deben aprenderse **exclusivamente con datos de entrenamiento**.

### Semilla fija

Todo proceso aleatorio debe usar `random_state=42` para reproducibilidad:

```python
# ✅ Correcto
mutual_info_classif(X, y, random_state=42)
train_test_split(X, y, random_state=42)
RandomForestClassifier(random_state=42)

# ❌ Incorrecto
mutual_info_classif(X, y)  # No reproducible
```

---

> **Fin del Documento 1** — Continuar con `Modelado_Validacion_Datathon_Banca.md` (Doc 2) usando los artefactos generados por esta guía.
