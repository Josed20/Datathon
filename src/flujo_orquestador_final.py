"""
Flujo orquestador final para el caso FinanCrece - ESAN 2026.

Objetivo:
- Resolver el requerimiento oficial como una herramienta de scoring:
  ingresar caracteristicas del solicitante, estimar prob_default y retornar
  una decision bajo la politica de riesgo.
- Usar solo dependencias disponibles en el runtime base: pandas, numpy,
  scikit-learn, joblib y openpyxl.
"""

from __future__ import annotations

import json
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import (
    ExtraTreesClassifier,
    GradientBoostingClassifier,
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    auc,
    brier_score_loss,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.utils.class_weight import compute_sample_weight

PROJECT_ROOT = Path(".")
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR.resolve()) not in sys.path:
    sys.path.insert(0, str(SRC_DIR.resolve()))

from feature_builder import build_features_german  # noqa: E402

TARGET_COL = "default_90d"
TARGET_RAW = "target"
TARGET_POSITIVE = "bad"
ID_COL = "id_cliente"
RANDOM_STATE = 42

TRAIN_PATH = PROJECT_ROOT / "dataInicial" / "dataset_credito-train.xlsx"
TEST_PATH = PROJECT_ROOT / "dataInicial" / "dataset_credito-test.xlsx"

REPORTS_DIR = PROJECT_ROOT / "reports"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)

GOOD_APPROVED = 450
GOOD_REJECTED = -150
BAD_APPROVED = -3000
BAD_REJECTED = 0
MEDIUM_EXPOSURE_FACTOR = 0.50


def make_one_hot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def ks_stat(y_true: pd.Series, y_proba: np.ndarray) -> float:
    frame = pd.DataFrame({"y": np.asarray(y_true), "p": y_proba}).sort_values(
        "p", ascending=False
    )
    positives = max(int((frame["y"] == 1).sum()), 1)
    negatives = max(int((frame["y"] == 0).sum()), 1)
    cum_pos = (frame["y"] == 1).cumsum() / positives
    cum_neg = (frame["y"] == 0).cumsum() / negatives
    return float((cum_pos - cum_neg).abs().max())


def lift_at_10(y_true: pd.Series, y_proba: np.ndarray) -> float:
    frame = pd.DataFrame({"y": np.asarray(y_true), "p": y_proba}).sort_values(
        "p", ascending=False
    )
    top_n = max(int(np.ceil(len(frame) * 0.10)), 1)
    base_rate = max(float(frame["y"].mean()), 1e-9)
    return float(frame.head(top_n)["y"].mean() / base_rate)


def evaluate_classifier(name: str, model: Pipeline, x_train, y_train, x_eval, y_eval) -> dict:
    p_train = model.predict_proba(x_train)[:, 1]
    p_eval = model.predict_proba(x_eval)[:, 1]
    pred_eval = (p_eval >= 0.50).astype(int)
    auc_train = roc_auc_score(y_train, p_train)
    auc_eval = roc_auc_score(y_eval, p_eval)
    precision, recall, _ = precision_recall_curve(y_eval, p_eval)
    return {
        "model": name,
        "auc_train": round(float(auc_train), 4),
        "auc_val": round(float(auc_eval), 4),
        "gini_val": round(float(2 * auc_eval - 1), 4),
        "ks_val": round(float(ks_stat(y_eval, p_eval)), 4),
        "pr_auc_val": round(float(auc(recall, precision)), 4),
        "brier_val": round(float(brier_score_loss(y_eval, p_eval)), 4),
        "lift10_val": round(float(lift_at_10(y_eval, p_eval)), 2),
        "f1_050": round(float(f1_score(y_eval, pred_eval, zero_division=0)), 4),
        "recall_050": round(float(recall_score(y_eval, pred_eval, zero_division=0)), 4),
        "precision_050": round(float(precision_score(y_eval, pred_eval, zero_division=0)), 4),
        "gap_train_val": round(float(abs(auc_train - auc_eval)), 4),
    }


def build_model_frame(df_raw: pd.DataFrame) -> pd.DataFrame:
    engineered = build_features_german(df_raw)
    exclude = {ID_COL, TARGET_RAW, TARGET_COL, "id_adicional", "Probabilidad"}
    raw_keep = [col for col in df_raw.columns if col not in exclude]
    new_cols = [col for col in engineered.columns if col not in df_raw.columns]
    return pd.concat([df_raw[[c for c in [ID_COL, TARGET_COL] if c in df_raw.columns]], df_raw[raw_keep], engineered[new_cols]], axis=1)


def split_feature_types(df_model: pd.DataFrame, feature_cols: list[str]) -> tuple[list[str], list[str]]:
    categorical = [
        col
        for col in feature_cols
        if str(df_model[col].dtype) in {"object", "category", "bool", "str", "string"}
    ]
    numeric = [col for col in feature_cols if col not in categorical]
    return numeric, categorical


def make_preprocessor(numeric_cols: list[str], categorical_cols: list[str]) -> ColumnTransformer:
    numeric_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", make_one_hot_encoder()),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipe, numeric_cols),
            ("cat", categorical_pipe, categorical_cols),
        ],
        remainder="drop",
    )


def make_candidates() -> dict:
    return {
        "Dummy_baseline": DummyClassifier(strategy="prior", random_state=RANDOM_STATE),
        "LogReg_balanced_C03": LogisticRegression(
            max_iter=2500,
            class_weight="balanced",
            C=0.3,
            random_state=RANDOM_STATE,
        ),
        "LogReg_balanced_C01": LogisticRegression(
            max_iter=2500,
            class_weight="balanced",
            C=0.1,
            random_state=RANDOM_STATE,
        ),
        "RandomForest_stable": RandomForestClassifier(
            n_estimators=350,
            max_depth=7,
            min_samples_leaf=8,
            class_weight="balanced_subsample",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "ExtraTrees_stable": ExtraTreesClassifier(
            n_estimators=350,
            max_depth=7,
            min_samples_leaf=8,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "HistGradientBoosting": HistGradientBoostingClassifier(
            max_iter=180,
            learning_rate=0.04,
            max_leaf_nodes=15,
            l2_regularization=0.20,
            random_state=RANDOM_STATE,
        ),
        "GradientBoosting_shallow": GradientBoostingClassifier(
            n_estimators=180,
            learning_rate=0.035,
            max_depth=2,
            subsample=0.85,
            random_state=RANDOM_STATE,
        ),
    }


def approval_roi(y_true: pd.Series, y_proba: np.ndarray, threshold: float) -> dict:
    y = np.asarray(y_true)
    reject = y_proba >= threshold
    approve = ~reject
    good = y == 0
    bad = y == 1
    good_approved = int((approve & good).sum())
    good_rejected = int((reject & good).sum())
    bad_approved = int((approve & bad).sum())
    bad_rejected = int((reject & bad).sum())
    benefit = (
        good_approved * GOOD_APPROVED
        + good_rejected * GOOD_REJECTED
        + bad_approved * BAD_APPROVED
        + bad_rejected * BAD_REJECTED
    )
    base = int(good.sum()) * GOOD_APPROVED + int(bad.sum()) * BAD_APPROVED
    return {
        "threshold": round(float(threshold), 4),
        "good_approved": good_approved,
        "good_rejected": good_rejected,
        "bad_approved": bad_approved,
        "bad_rejected": bad_rejected,
        "benefit_usd": round(float(benefit), 2),
        "base_benefit_usd": round(float(base), 2),
        "incremental_saving_usd": round(float(benefit - base), 2),
        "roi_vs_base": round(float((benefit - base) / max(abs(base), 1)), 4),
        "recall_default": round(float(bad_rejected / max(bad.sum(), 1)), 4),
        "approval_rate": round(float(approve.mean()), 4),
    }


def optimize_binary_threshold(y_true: pd.Series, y_proba: np.ndarray) -> pd.DataFrame:
    grid = np.round(np.arange(0.05, 0.91, 0.01), 2)
    return pd.DataFrame([approval_roi(y_true, y_proba, t) for t in grid]).sort_values(
        ["benefit_usd", "recall_default"], ascending=[False, False]
    )


def three_band_policy(y_true: pd.Series, y_proba: np.ndarray) -> tuple[dict, pd.DataFrame]:
    candidates = []
    for low in np.arange(0.10, 0.31, 0.01):
        for high in np.arange(0.32, 0.71, 0.01):
            if high <= low + 0.05:
                continue
            low_mask = y_proba < low
            mid_mask = (y_proba >= low) & (y_proba < high)
            high_mask = y_proba >= high
            y = np.asarray(y_true)
            benefit = 0.0
            benefit += int(((y == 0) & low_mask).sum()) * GOOD_APPROVED
            benefit += int(((y == 1) & low_mask).sum()) * BAD_APPROVED
            benefit += int(((y == 0) & mid_mask).sum()) * (GOOD_APPROVED * MEDIUM_EXPOSURE_FACTOR)
            benefit += int(((y == 1) & mid_mask).sum()) * (BAD_APPROVED * MEDIUM_EXPOSURE_FACTOR)
            benefit += int(((y == 0) & high_mask).sum()) * GOOD_REJECTED
            benefit += int(((y == 1) & high_mask).sum()) * BAD_REJECTED
            candidates.append(
                {
                    "u_bajo": round(float(low), 2),
                    "u_alto": round(float(high), 2),
                    "beneficio_3_bandas_usd": round(float(benefit), 2),
                    "clientes_bajo": int(low_mask.sum()),
                    "clientes_medio": int(mid_mask.sum()),
                    "clientes_alto": int(high_mask.sum()),
                    "pct_bajo": round(float(low_mask.mean() * 100), 2),
                    "pct_medio": round(float(mid_mask.mean() * 100), 2),
                    "pct_alto": round(float(high_mask.mean() * 100), 2),
                    "tasa_default_bajo": round(float(y[low_mask].mean()), 4) if low_mask.sum() else 0.0,
                    "tasa_default_medio": round(float(y[mid_mask].mean()), 4) if mid_mask.sum() else 0.0,
                    "tasa_default_alto": round(float(y[high_mask].mean()), 4) if high_mask.sum() else 0.0,
                }
            )
    ranking = pd.DataFrame(candidates).sort_values("beneficio_3_bandas_usd", ascending=False)
    best = ranking.iloc[0].to_dict()
    best.update(
        {
            "decision_bajo": "APROBAR linea completa",
            "decision_medio": "CONDICIONAR linea al 50% o revision manual",
            "decision_alto": "RECHAZAR o exigir mitigantes",
            "nota": "Politica optimizada en validacion; valores economicos bajo supuestos documentados.",
        }
    )
    return best, ranking


def fit_candidate(name: str, estimator, preprocessor, x_train, y_train) -> Pipeline:
    pipe = Pipeline(
        steps=[
            ("preprocessor", clone(preprocessor)),
            ("model", clone(estimator)),
        ]
    )
    if name in {"HistGradientBoosting", "GradientBoosting_shallow"}:
        weights = compute_sample_weight("balanced", y_train)
        pipe.fit(x_train, y_train, model__sample_weight=weights)
    else:
        pipe.fit(x_train, y_train)
    return pipe


def main() -> None:
    print("== FASE 0: carga y validacion del caso oficial ==")
    df_raw = pd.read_excel(TRAIN_PATH, engine="openpyxl")
    df_test_raw = pd.read_excel(TEST_PATH, engine="openpyxl")
    df_raw[TARGET_COL] = (df_raw[TARGET_RAW] == TARGET_POSITIVE).astype(int)
    print(f"Train: {df_raw.shape} | Test oficial: {df_test_raw.shape}")
    print(f"Default rate train: {df_raw[TARGET_COL].mean():.2%}")

    print("\n== FASE 1: features reproducibles ==")
    df_model = build_model_frame(df_raw)
    df_test_model = build_model_frame(df_test_raw)
    feature_cols = [
        col
        for col in df_model.columns
        if col not in {ID_COL, TARGET_COL, TARGET_RAW, "id_adicional", "Probabilidad"}
    ]
    numeric_cols, categorical_cols = split_feature_types(df_model, feature_cols)
    print(f"Features: {len(feature_cols)} | numericas: {len(numeric_cols)} | categoricas: {len(categorical_cols)}")

    X = df_model[feature_cols]
    y = df_model[TARGET_COL]
    X_sub = df_test_model.reindex(columns=feature_cols)

    x_train_full, x_test, y_train_full, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        stratify=y,
        random_state=RANDOM_STATE,
    )
    x_train, x_val, y_train, y_val = train_test_split(
        x_train_full,
        y_train_full,
        test_size=0.25,
        stratify=y_train_full,
        random_state=RANDOM_STATE,
    )

    print("\n== FASE 2: comparacion de modelos ==")
    preprocessor = make_preprocessor(numeric_cols, categorical_cols)
    rows = []
    fitted = {}
    for name, estimator in make_candidates().items():
        model = fit_candidate(name, estimator, preprocessor, x_train, y_train)
        metrics = evaluate_classifier(name, model, x_train, y_train, x_val, y_val)
        # Penaliza sobreajuste y mala calibracion, sin mirar test interno.
        overfit_penalty = max(metrics["gap_train_val"] - 0.06, 0) * 0.45
        brier_penalty = metrics["brier_val"] * 0.04
        metrics["selection_score"] = round(metrics["auc_val"] - overfit_penalty - brier_penalty, 5)
        rows.append(metrics)
        fitted[name] = model
        print(
            f"{name:24s} AUC={metrics['auc_val']:.4f} "
            f"Gini={metrics['gini_val']:.4f} KS={metrics['ks_val']:.4f} "
            f"Brier={metrics['brier_val']:.4f} Gap={metrics['gap_train_val']:.4f} "
            f"Score={metrics['selection_score']:.5f}"
        )

    comparison = pd.DataFrame(rows).sort_values("selection_score", ascending=False)
    comparison.to_csv(REPORTS_DIR / "model_comparison_orquestador.csv", index=False)
    champion_name = str(comparison.iloc[0]["model"])
    champion_val = fitted[champion_name]
    print(f"\nCampeon por score auditor: {champion_name}")

    print("\n== FASE 3: validacion holdout interna ==")
    test_metrics = evaluate_classifier(champion_name, champion_val, x_train, y_train, x_test, y_test)
    print(
        f"Test interno: AUC={test_metrics['auc_val']:.4f} "
        f"Gini={test_metrics['gini_val']:.4f} KS={test_metrics['ks_val']:.4f} "
        f"Brier={test_metrics['brier_val']:.4f}"
    )

    y_val_proba = champion_val.predict_proba(x_val)[:, 1]
    threshold_grid = optimize_binary_threshold(y_val, y_val_proba)
    threshold_grid.to_csv(REPORTS_DIR / "threshold_analysis_orquestador.csv", index=False)
    best_threshold = threshold_grid.iloc[0].to_dict()

    policy, policy_grid = three_band_policy(y_val, y_val_proba)
    policy_grid.to_csv(REPORTS_DIR / "politica_3_bandas_grid_orquestador.csv", index=False)
    pd.DataFrame([policy]).to_csv(REPORTS_DIR / "politica_3_bandas_orquestador.csv", index=False)

    print("\n== FASE 4: politica de riesgo ==")
    print(f"Threshold binario optimo: {best_threshold['threshold']} | ahorro={best_threshold['incremental_saving_usd']:,.0f}")
    print(
        f"3 bandas: bajo < {policy['u_bajo']:.2f}, alto >= {policy['u_alto']:.2f} | "
        f"beneficio={policy['beneficio_3_bandas_usd']:,.0f}"
    )

    print("\n== FASE 5: entrenamiento final y herramienta de scoring ==")
    selected_estimator = deepcopy(make_candidates()[champion_name])
    final_model = fit_candidate(champion_name, selected_estimator, preprocessor, X, y)
    official_proba = final_model.predict_proba(X_sub)[:, 1]
    submission = pd.DataFrame(
        {
            ID_COL: df_test_raw[ID_COL].values,
            "prob_default": official_proba,
        }
    )
    submission.to_csv(PROJECT_ROOT / "submission.csv", index=False)

    artifact = {
        "model": final_model,
        "model_name": champion_name,
        "feature_columns": feature_cols,
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "target_col": TARGET_COL,
        "target_mapping": {"good": 0, "bad": 1},
        "policy": {
            "u_bajo": float(policy["u_bajo"]),
            "u_alto": float(policy["u_alto"]),
            "decision_bajo": policy["decision_bajo"],
            "decision_medio": policy["decision_medio"],
            "decision_alto": policy["decision_alto"],
        },
        "business_values": {
            "good_approved": GOOD_APPROVED,
            "good_rejected": GOOD_REJECTED,
            "bad_approved": BAD_APPROVED,
            "bad_rejected": BAD_REJECTED,
            "medium_exposure_factor": MEDIUM_EXPOSURE_FACTOR,
        },
        "created_at": datetime.now().isoformat(),
    }
    joblib.dump(artifact, MODELS_DIR / "scoring_tool.joblib")

    report = {
        "status": "READY",
        "official_requirement": "Herramienta que recibe caracteristicas, estima probabilidad de default y decide aprobacion segun politica de riesgo.",
        "champion_model": champion_name,
        "selection_table": comparison.to_dict(orient="records"),
        "validation_metrics": comparison.iloc[0].to_dict(),
        "internal_test_metrics": test_metrics,
        "best_binary_threshold": best_threshold,
        "three_band_policy": policy,
        "submission": {
            "path": "submission.csv",
            "rows": int(len(submission)),
            "prob_min": round(float(submission["prob_default"].min()), 6),
            "prob_mean": round(float(submission["prob_default"].mean()), 6),
            "prob_max": round(float(submission["prob_default"].max()), 6),
        },
        "artifacts": {
            "scoring_tool": "models/scoring_tool.joblib",
            "comparison": "reports/model_comparison_orquestador.csv",
            "thresholds": "reports/threshold_analysis_orquestador.csv",
            "policy": "reports/politica_3_bandas_orquestador.csv",
        },
        "warnings": [
            "No hay columna temporal oficial; se usa split estratificado anti-leakage.",
            "Variables como ingreso, buro externo y geografia no existen en el Excel oficial.",
            "La politica financiera usa matriz economica/supuestos documentados.",
        ],
    }
    with open(REPORTS_DIR / "scoring_tool_report.json", "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False, default=str)

    print("\n== ENTREGABLES GENERADOS ==")
    print("models/scoring_tool.joblib")
    print("reports/scoring_tool_report.json")
    print("reports/model_comparison_orquestador.csv")
    print("reports/politica_3_bandas_orquestador.csv")
    print("submission.csv")
    print(
        f"Submission: rows={len(submission)} "
        f"prob_min={submission['prob_default'].min():.4f} "
        f"prob_mean={submission['prob_default'].mean():.4f} "
        f"prob_max={submission['prob_default'].max():.4f}"
    )


if __name__ == "__main__":
    main()
