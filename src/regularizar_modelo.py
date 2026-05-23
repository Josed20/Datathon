"""
Regularización del modelo campeón y generación del Notebook de entrega
Datathon FinanCrece — ESAN 2026

Objetivo: reducir overfitting gap de LightGBM (actual ~0.12)
Estrategia: más regularización + Logistic Regression como modelo 2do
"""

import pandas as pd
import numpy as np
import json
import joblib
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
PROJECT_ROOT = Path(".")

# Cargar datos y preprocessor ya ajustados
print("Cargando datos y preprocessor...")
df_fe = pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "features.parquet")
df_fe_test = pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "features_test.parquet")
preprocessor = joblib.load(PROJECT_ROOT / "models" / "preprocessor.joblib")

with open(PROJECT_ROOT / "models" / "model_metadata.json") as f:
    metadata = json.load(f)

TARGET_COL = "default_90d"
ID_COLS = ["id_cliente"]
RANDOM_STATE = 42

excl = ["id_cliente", "target", TARGET_COL, "id_adicional", "Probabilidad"]
model_features = [c for c in df_fe.columns if c not in excl]

X = df_fe[model_features]
y = df_fe[TARGET_COL]

from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, brier_score_loss, precision_recall_curve, auc

X_train_full, X_test, y_train_full, y_test = train_test_split(
    X, y, test_size=0.20, random_state=RANDOM_STATE, stratify=y
)
X_train, X_val, y_train, y_val = train_test_split(
    X_train_full, y_train_full, test_size=0.25, random_state=RANDOM_STATE, stratify=y_train_full
)

X_train_proc = preprocessor.transform(X_train)
X_val_proc   = preprocessor.transform(X_val)
X_test_proc  = preprocessor.transform(X_test)

X_sub = df_fe_test[[c for c in model_features if c in df_fe_test.columns]]
for c in model_features:
    if c not in X_sub.columns:
        X_sub[c] = 0
X_sub = X_sub[model_features]
X_sub_proc = preprocessor.transform(X_sub)

pos_weight = (len(y_train) - y_train.sum()) / y_train.sum()

print(f"Train: {X_train.shape} | Val: {X_val.shape} | Test: {X_test.shape}")

def ks_stat(y_true, y_proba):
    df_t = pd.DataFrame({"r": np.array(y_true), "p": y_proba}).sort_values("p", ascending=False)
    cp = (df_t["r"]==1).cumsum() / max((df_t["r"]==1).sum(), 1)
    cn = (df_t["r"]==0).cumsum() / max((df_t["r"]==0).sum(), 1)
    return float((cp - cn).abs().max())

def lift10(y_true, y_proba):
    df_t = pd.DataFrame({"r": np.array(y_true), "p": y_proba}).sort_values("p", ascending=False)
    n10 = max(int(len(df_t)*0.1), 1)
    return float(df_t.head(n10)["r"].mean() / max(df_t["r"].mean(), 1e-6))

def evaluar_rapido(model, Xtr, ytr, Xva, yva, nom):
    p_tr = model.predict_proba(Xtr)[:,1]
    p_va = model.predict_proba(Xva)[:,1]
    a_tr = roc_auc_score(ytr, p_tr)
    a_va = roc_auc_score(yva, p_va)
    print(f"  {nom}: AUC_val={a_va:.4f} | Gini={2*a_va-1:.4f} | KS={ks_stat(yva,p_va):.4f} | Gap={abs(a_tr-a_va):.4f} | Brier={brier_score_loss(yva,p_va):.4f}")
    return a_va, abs(a_tr - a_va)

# ============================================================
# REGULARIZACIÓN DE LIGHTGBM
# ============================================================
print("\n=== REGULARIZACIÓN DE LightGBM ===")

import lightgbm as lgb

configs_lgb = [
    {"nombre": "LGB_reg_v1", "params": {
        "n_estimators": 300, "learning_rate": 0.05, "max_depth": 4, "num_leaves": 15,
        "scale_pos_weight": pos_weight, "min_child_samples": 30, "reg_alpha": 0.5,
        "reg_lambda": 1.0, "subsample": 0.8, "colsample_bytree": 0.8,
        "random_state": RANDOM_STATE, "n_jobs": -1, "verbosity": -1,
    }},
    {"nombre": "LGB_reg_v2", "params": {
        "n_estimators": 400, "learning_rate": 0.03, "max_depth": 5, "num_leaves": 20,
        "scale_pos_weight": pos_weight, "min_child_samples": 20, "reg_alpha": 0.3,
        "reg_lambda": 0.5, "subsample": 0.85, "colsample_bytree": 0.85,
        "random_state": RANDOM_STATE, "n_jobs": -1, "verbosity": -1,
    }},
    {"nombre": "LGB_reg_v3_balanced", "params": {
        "n_estimators": 300, "learning_rate": 0.05, "max_depth": 4, "num_leaves": 15,
        "is_unbalance": True, "min_child_samples": 30, "reg_alpha": 0.5,
        "reg_lambda": 1.0, "subsample": 0.8, "colsample_bytree": 0.8,
        "random_state": RANDOM_STATE, "n_jobs": -1, "verbosity": -1,
    }},
]

best_lgb_auc = 0
best_lgb_model = None
best_lgb_name = ""

for cfg in configs_lgb:
    m = lgb.LGBMClassifier(**cfg["params"])
    m.fit(X_train_proc, y_train, eval_set=[(X_val_proc, y_val)],
          callbacks=[lgb.early_stopping(40, verbose=False)])
    a_va, gap = evaluar_rapido(m, X_train_proc, y_train, X_val_proc, y_val, cfg["nombre"])
    if a_va > best_lgb_auc:
        best_lgb_auc = a_va
        best_lgb_model = m
        best_lgb_name = cfg["nombre"]

print(f"\nMejor LGB regularizado: {best_lgb_name} | AUC={best_lgb_auc:.4f}")

# Comparar con Logistic Regression (más interpretable y más estable)
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

print("\n=== COMPARACIÓN MODELOS ESTABLES ===")
lr_c = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE, C=0.3, n_jobs=-1)
lr_c.fit(X_train_proc, y_train)
lr_auc, lr_gap = evaluar_rapido(lr_c, X_train_proc, y_train, X_val_proc, y_val, "LogReg_C0.3")

lr_c2 = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE, C=0.1, n_jobs=-1)
lr_c2.fit(X_train_proc, y_train)
lr2_auc, lr2_gap = evaluar_rapido(lr_c2, X_train_proc, y_train, X_val_proc, y_val, "LogReg_C0.1")

rf_small = RandomForestClassifier(n_estimators=200, max_depth=7, min_samples_leaf=8,
                                   class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1)
rf_small.fit(X_train_proc, y_train)
rf_auc, rf_gap = evaluar_rapido(rf_small, X_train_proc, y_train, X_val_proc, y_val, "RF_depth7")

# ============================================================
# SELECCIÓN FINAL: Mejor trade-off AUC + Gap
# ============================================================
print("\n=== SELECCIÓN DEL MODELO FINAL ===")
candidatos = [
    {"nombre": "LGB_regularizado", "modelo": best_lgb_model, "auc": best_lgb_auc},
    {"nombre": "LogReg_C0.3", "modelo": lr_c, "auc": lr_auc},
    {"nombre": "LogReg_C0.1", "modelo": lr_c2, "auc": lr2_auc},
    {"nombre": "RF_depth7", "modelo": rf_small, "auc": rf_auc},
]

# Si el mejor LGB regularizado tiene AUC > LogReg + 0.02 → usar LGB
# De lo contrario, usar el que tenga mejor AUC con gap < 0.10
champion_name = best_lgb_name
champion = best_lgb_model
champion_auc = best_lgb_auc

for c in candidatos:
    a = c["auc"]
    _, g = evaluar_rapido(c["modelo"], X_train_proc, y_train, X_val_proc, y_val, f"→ {c['nombre']}")
    if a >= champion_auc - 0.02 and g < 0.10:
        if a > champion_auc or (a == champion_auc and g < 0.10):
            champion = c["modelo"]
            champion_name = c["nombre"]
            champion_auc = a
            print(f"  ↗ Nuevo campeón provisional: {champion_name} (AUC={a:.4f}, Gap={g:.4f})")

print(f"\n✅ CAMPEÓN FINAL: {champion_name} | AUC_val={champion_auc:.4f}")

# Métricas finales del campeón en validación y test
y_proba_val = champion.predict_proba(X_val_proc)[:,1]
y_proba_test = champion.predict_proba(X_test_proc)[:,1]

auc_val_f = roc_auc_score(y_val, y_proba_val)
ks_val_f = ks_stat(y_val, y_proba_val)
brier_val_f = brier_score_loss(y_val, y_proba_val)
p_va, r_va, _ = precision_recall_curve(y_val, y_proba_val)
prauc_val_f = auc(r_va, p_va)

auc_test_f = roc_auc_score(y_test, y_proba_test)
gap_f = abs(auc_val_f - auc_test_f)

auc_tr_f = roc_auc_score(y_train, champion.predict_proba(X_train_proc)[:,1])
gap_tr_val = abs(auc_tr_f - auc_val_f)

print(f"\n📊 MÉTRICAS FINALES:")
print(f"  AUC Train:  {auc_tr_f:.4f}")
print(f"  AUC Val:    {auc_val_f:.4f}")
print(f"  AUC Test:   {auc_test_f:.4f}")
print(f"  Gap Tr/Val: {gap_tr_val:.4f}")
print(f"  Gap Val/Test: {gap_f:.4f}")
print(f"  Gini Val:   {2*auc_val_f-1:.4f}")
print(f"  KS Val:     {ks_val_f:.4f}")
print(f"  Brier Val:  {brier_val_f:.4f}")
print(f"  PR-AUC Val: {prauc_val_f:.4f}")
print(f"  Lift@10%:   {lift10(y_val, y_proba_val):.2f}x")

# Guardar modelos actualizados
joblib.dump(champion, PROJECT_ROOT / "models" / "best_model.joblib")
print(f"\n✅ best_model.joblib actualizado → {champion_name}")

# Actualizar metadata
metadata.update({
    "model_name": champion_name,
    "metricas_val": {
        "roc_auc": round(float(auc_val_f), 4),
        "gini": round(float(2*auc_val_f-1), 4),
        "ks": round(float(ks_val_f), 4),
        "brier": round(float(brier_val_f), 4),
        "pr_auc": round(float(prauc_val_f), 4),
        "lift_at_10": round(float(lift10(y_val, y_proba_val)), 2),
        "overfitting_gap": round(float(gap_tr_val), 4),
    },
    "metricas_test_interno": {
        "roc_auc": round(float(auc_test_f), 4),
        "gini": round(float(2*auc_test_f-1), 4),
        "gap_val_test": round(float(gap_f), 4),
    }
})
with open(PROJECT_ROOT / "models" / "model_metadata.json", "w") as f:
    json.dump(metadata, f, indent=2, default=str)

# Regenerar submission con el modelo final
print("\n=== REGENERANDO SUBMISSION.CSV ===")
y_sub = champion.predict_proba(X_sub_proc)[:,1]
submission = pd.DataFrame({
    "id_cliente": df_fe_test["id_cliente"].values,
    "prob_default": y_sub,
})
submission.to_csv(PROJECT_ROOT / "submission.csv", index=False)
print(f"✅ submission.csv regenerado con {champion_name}")
print(f"   Stats: min={y_sub.min():.4f} | mean={y_sub.mean():.4f} | max={y_sub.max():.4f}")
print(submission.head().to_string(index=False))

print("\n🏁 Regularización completada")
