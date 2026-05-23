"""
Herramienta de scoring para FinanCrece - ESAN 2026.

Uso:
  python src/herramienta_scoring.py --input solicitud_ejemplo_scoring.json
  python src/herramienta_scoring.py --input dataInicial/dataset_credito-test.xlsx --output reports/scoring_batch.csv

Retorna prob_default, banda de riesgo y decision de politica.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib
import pandas as pd

PROJECT_ROOT = Path(".")
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR.resolve()) not in sys.path:
    sys.path.insert(0, str(SRC_DIR.resolve()))

from feature_builder import build_features_german  # noqa: E402

ARTIFACT_PATH = PROJECT_ROOT / "models" / "scoring_tool.joblib"


def load_input(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".json":
        with open(path, "r", encoding="utf-8") as file:
            payload = json.load(file)
        if isinstance(payload, dict):
            payload = [payload]
        return pd.DataFrame(payload)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path, engine="openpyxl")
    if suffix == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"Formato no soportado: {suffix}. Use JSON, XLSX o CSV.")


def build_model_input(df_raw: pd.DataFrame, feature_columns: list[str]) -> pd.DataFrame:
    engineered = build_features_german(df_raw)
    exclude = {"id_cliente", "target", "default_90d", "id_adicional", "Probabilidad"}
    raw_keep = [col for col in df_raw.columns if col not in exclude]
    new_cols = [col for col in engineered.columns if col not in df_raw.columns]
    model_frame = pd.concat([df_raw[raw_keep], engineered[new_cols]], axis=1)
    return model_frame.reindex(columns=feature_columns)


def assign_policy(prob: float, policy: dict) -> tuple[str, str]:
    if prob < policy["u_bajo"]:
        return "Bajo", policy["decision_bajo"]
    if prob < policy["u_alto"]:
        return "Medio", policy["decision_medio"]
    return "Alto", policy["decision_alto"]


def explain_business_flags(row: pd.Series) -> str:
    flags: list[str] = []
    if row.get("checking_status") in {"<0", "0<=X<200"}:
        flags.append("liquidez_debil")
    if row.get("credit_history") in {"no credits/all paid", "all paid"}:
        flags.append("historial_crediticio_riesgoso")
    if row.get("savings_status") in {"<100", "100<=X<500"}:
        flags.append("bajo_colchon_ahorro")
    if row.get("employment") in {"unemployed", "<1"}:
        flags.append("estabilidad_laboral_baja")
    try:
        if float(row.get("duration", 0)) > 24:
            flags.append("plazo_largo")
    except (TypeError, ValueError):
        pass
    try:
        if float(row.get("credit_amount", 0)) > 5000:
            flags.append("monto_alto")
    except (TypeError, ValueError):
        pass
    return ";".join(flags[:4]) if flags else "sin_alertas_fuertes"


def score(df_raw: pd.DataFrame, artifact: dict) -> pd.DataFrame:
    model_input = build_model_input(df_raw, artifact["feature_columns"])
    probabilities = artifact["model"].predict_proba(model_input)[:, 1]
    rows = []
    for idx, prob in enumerate(probabilities):
        band, decision = assign_policy(float(prob), artifact["policy"])
        rows.append(
            {
                "id_cliente": df_raw.iloc[idx].get("id_cliente", idx + 1),
                "prob_default": round(float(prob), 6),
                "banda_riesgo": band,
                "decision_politica": decision,
                "factores_alerta": explain_business_flags(df_raw.iloc[idx]),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Herramienta de scoring crediticio FinanCrece.")
    parser.add_argument("--input", required=True, help="Archivo JSON, CSV o XLSX con solicitudes.")
    parser.add_argument("--output", default=None, help="Ruta CSV de salida para scoring batch.")
    args = parser.parse_args()

    if not ARTIFACT_PATH.exists():
        raise FileNotFoundError(
            "No existe models/scoring_tool.joblib. Ejecute primero src/flujo_orquestador_final.py."
        )

    artifact = joblib.load(ARTIFACT_PATH)
    df_raw = load_input(Path(args.input))
    result = score(df_raw, artifact)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(output_path, index=False)
        print(f"Scoring guardado en {output_path}")

    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
