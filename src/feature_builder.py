"""
feature_builder.py — Transformaciones reproducibles fila a fila
Datathon FinanCrece S.A. — ESAN 2026

Aplicar IGUAL a train y test. Sin fit de parámetros del dataset.
"""
import pandas as pd
import numpy as np


def build_features_german(df_input: pd.DataFrame) -> pd.DataFrame:
    """
    Feature engineering adaptado al German Credit Dataset para FinanCrece S.A.
    Solo transformaciones fila a fila — sin fit de parámetros.
    Reproducible para train y test.
    
    Returns:
        DataFrame con features nuevas (sin las originales).
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

    # --- 3. CARGA FINANCIERA ---
    if "duration" in df_input.columns and "credit_amount" in df_input.columns:
        fe["carga_financiera"] = df_input["credit_amount"] * df_input["duration"]
        fe["log_carga"] = np.log1p(fe["carga_financiera"])
        fe["cuota_estimada"] = df_input["credit_amount"] / df_input["duration"].clip(lower=1)
        fe["log_cuota"] = np.log1p(fe["cuota_estimada"])

    # --- 4. CHECKING STATUS ---
    checking_risk = {"<0": 3, "0<=X<200": 2, ">=200": 1, "no checking": 0}
    if "checking_status" in df_input.columns:
        fe["checking_risk_ordinal"] = df_input["checking_status"].map(checking_risk).fillna(2)
        fe["sin_cuenta_corriente"] = (df_input["checking_status"] == "no checking").astype(int)
        fe["cuenta_negativa"] = (df_input["checking_status"] == "<0").astype(int)
        fe["cuenta_baja"] = (df_input["checking_status"] == "0<=X<200").astype(int)
        fe["cuenta_buena"] = (df_input["checking_status"] == ">=200").astype(int)

    # --- 5. HISTORIAL CREDITICIO ---
    history_risk = {
        "no credits/all paid": 4,
        "all paid": 3,
        "existing paid": 2,
        "delayed previously": 2,
        "critical/other existing credit": 1,
    }
    if "credit_history" in df_input.columns:
        fe["history_risk_ordinal"] = df_input["credit_history"].map(history_risk).fillna(2)
        fe["historial_limpio"] = (df_input["credit_history"] == "existing paid").astype(int)
        fe["historial_critico"] = df_input["credit_history"].isin(
            ["no credits/all paid", "all paid"]
        ).astype(int)
        fe["historial_delay"] = (df_input["credit_history"] == "delayed previously").astype(int)

    # --- 6. SAVINGS STATUS ---
    savings_risk = {"<100": 4, "100<=X<500": 3, "500<=X<1000": 2, ">=1000": 1, "no known savings": 0}
    if "savings_status" in df_input.columns:
        fe["savings_risk_ordinal"] = df_input["savings_status"].map(savings_risk).fillna(2)
        fe["sin_ahorros"] = (df_input["savings_status"] == "<100").astype(int)
        fe["ahorros_altos"] = df_input["savings_status"].isin([">=1000", "no known savings"]).astype(int)

    # --- 7. EMPLEO ---
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

    # --- 9. COMPROMISO DE CUOTA ---
    if "installment_commitment" in df_input.columns:
        fe["cuota_alta_pct"] = (df_input["installment_commitment"] >= 4).astype(int)
        fe["cuota_baja_pct"] = (df_input["installment_commitment"] <= 2).astype(int)

    # --- 10. INTERACCIONES ---
    if "checking_risk_ordinal" in fe.columns and "history_risk_ordinal" in fe.columns:
        fe["riesgo_combinado"] = fe["checking_risk_ordinal"] * fe["history_risk_ordinal"]
    if "cuenta_negativa" in fe.columns and "monto_alto" in fe.columns:
        fe["negativo_y_monto_alto"] = (fe["cuenta_negativa"] & fe["monto_alto"]).astype(int)
    if "joven" in fe.columns and "historial_limpio" in fe.columns and "monto_alto" in fe.columns:
        fe["joven_riesgo_alto"] = (
            fe["joven"] & ~fe["historial_limpio"].astype(bool) & fe["monto_alto"]
        ).astype(int)
    if "sin_ahorros" in fe.columns and "cuenta_negativa" in fe.columns:
        fe["sin_reservas"] = (fe["sin_ahorros"] & fe["cuenta_negativa"]).astype(int)
    if "carga_financiera" in fe.columns and "checking_risk_ordinal" in fe.columns:
        safe_check = (4 - fe["checking_risk_ordinal"]).clip(lower=0.1)
        fe["carga_vs_cuenta"] = fe["log_carga"] / safe_check

    # --- 11. PROPÓSITO DEL CRÉDITO ---
    purpose_risk_high = ["new car", "furniture/equipment", "radio/tv"]
    purpose_risk_low = ["business", "education", "repairs"]
    if "purpose" in df_input.columns:
        fe["proposito_consumo"] = df_input["purpose"].isin(purpose_risk_high).astype(int)
        fe["proposito_productivo"] = df_input["purpose"].isin(purpose_risk_low).astype(int)

    # --- 12. GÉNERO/ESTADO CIVIL ---
    if "personal_status" in df_input.columns:
        fe["es_mujer"] = df_input["personal_status"].str.contains(
            "female", case=False, na=False
        ).astype(int)
        fe["divorciado_hombre"] = (df_input["personal_status"] == "male div/sep").astype(int)

    # --- 13. HOUSING ---
    housing_risk = {"rent": 2, "for free": 1, "own": 0}
    if "housing" in df_input.columns:
        fe["housing_risk"] = df_input["housing"].map(housing_risk).fillna(1)

    # --- 14. SCORE DE RIESGO COMPUESTO ---
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


def prepare_dataset(df_raw: pd.DataFrame, target_col: str = None) -> pd.DataFrame:
    """
    Pipeline completo de preparación: feature engineering + consolidación.
    
    Args:
        df_raw: Dataset raw (train o test)
        target_col: Nombre de la columna target (None para test)
    Returns:
        Dataset consolidado con features originales + nuevas
    """
    fe = build_features_german(df_raw)
    
    # Columnas a excluir del consolidado
    exclude = ["target"]
    if target_col:
        exclude.append(target_col)
    
    raw_keep = [c for c in df_raw.columns if c not in exclude]
    new_fe = [c for c in fe.columns if c not in df_raw.columns]
    
    df_out = pd.concat([df_raw[raw_keep], fe[new_fe]], axis=1)
    return df_out
