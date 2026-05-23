"""
FASE 0 — EXTRACCIÓN DEL CASO
Datathon FinanCrece S.A. — ESAN 2026
Auditor Senior de Machine Learning / Scoring de Crédito Bancario
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(".")

# ============================================================
# PARÁMETROS AUTORITATIVOS DEL CASO (extraídos del PDF oficial)
# ============================================================
case_config = {
    # --- Información del evento ---
    "datathon_name": "Datathon ESAN 2026",
    "empresa_caso": "FinanCrece S.A.",
    "pais": "Perú",
    "regulador": "SBS (Superintendencia de Banca y Seguros)",
    "fecha_evento": "2026-05-23",
    "hora_limite": "15:30",
    "tiempo_disponible_horas": 3,
    "email_envio": "datafest@esan.edu.pe",
    
    # --- Problema técnico ---
    "tipo_problema": "clasificacion_binaria",
    "target_col": "default_90d",
    "target_raw_col": "target",
    "target_mapping": {"good": 0, "bad": 1},
    "target_descripcion": "Dataset oficial: target='bad' se mapea a default_90d=1; target='good' se mapea a default_90d=0",
    "id_cols": ["id_cliente"],
    
    # --- Métricas del jurado ---
    "metrica_jurado": "roc_auc",
    "metricas_secundarias": ["ks", "gini", "brier_score", "lift_at_10", "pr_auc"],
    "criterios_jurado": {
        "calidad_modelo": 0.30,
        "interpretabilidad": 0.25,
        "impacto_negocio": 0.25,
        "presentacion_oral": 0.20
    },
    
    # --- Datos ---
    "data_train_path": "dataInicial/dataset_credito-train.xlsx",
    "data_test_path": "dataInicial/dataset_credito-test.xlsx",
    "data_train_rows": 800,
    "data_test_rows": 200,
    "data_train_cols": 22,
    "data_test_cols": 23,
    "dataset_oficial": "German Credit adaptado por el caso oficial FinanCrece",
    "submission_cols": ["id_cliente", "prob_default"],
    "submission_format": "csv",
    
    # --- Estrategia de validación ---
    "validation_strategy": "stratified_split",
    "nota_validacion": "Sin columna de fecha/periodo confirmada en datos reales; usar stratified_split anti-leakage",
    "test_size": 0.20,
    "val_size": 0.25,
    "random_state": 42,
    
    # --- Contexto de negocio ---
    "problema_negocio": "Incremento de mora del 4.2% al 7.8% (+3.6pp) en 18 meses erosiona rentabilidad",
    "objetivo_negocio": "Política de 3 bandas de riesgo para reducir mora sin destruir originación",
    "metrica_negocio_principal": "ROI Financiero Neto",
    
    # --- Matriz económica FinanCrece S.A. ---
    "matriz_economica": {
        "VN_buen_aprobado": 450,
        "FP_buen_rechazado": -150,
        "FN_default_aprobado": -3000,
        "VP_default_rechazado": 0,
        "factor_exposicion_media": 0.50,
        "nota": "Todos los valores en USD. VN=True Negative (pagador aprobado), FP=False Positive (pagador rechazado erróneamente), FN=False Negative (moroso aprobado), VP=True Positive (default evitado)"
    },
    
    # --- Variables clave del caso ---
    "variables_clave": {
        "id_cliente": "ID único del cliente — excluir del entrenamiento y usar en submission",
        "id_adicional": "ID auxiliar presente solo en test — no usar para entrenar",
        "target": "Columna raw del train: good/bad",
        "default_90d": "TARGET canónico derivado: 0=good/pagador, 1=bad/default",
        "Probabilidad": "Columna vacía del test oficial; el entregable final usa prob_default",
        "checking_status": "Estado de cuenta corriente; señal fuerte de liquidez/riesgo",
        "duration": "Duración del préstamo en meses",
        "credit_history": "Historial crediticio del solicitante",
        "purpose": "Destino del crédito",
        "credit_amount": "Monto del crédito solicitado",
        "savings_status": "Nivel de ahorros declarados",
        "employment": "Antigüedad/estabilidad laboral",
        "installment_commitment": "Porcentaje de ingreso comprometido al pago",
        "personal_status": "Estado civil/género codificado en el dataset",
        "other_parties": "Garantes/co-deudores",
        "residence_since": "Tiempo de residencia",
        "property_magnitude": "Tipo/magnitud de propiedad",
        "age": "Edad del solicitante",
        "other_payment_plans": "Otros planes de pago",
        "housing": "Situación de vivienda",
        "existing_credits": "Número de créditos existentes",
        "job": "Tipo de empleo/oficio",
        "num_dependents": "Número de dependientes",
        "own_telephone": "Tenencia de teléfono",
        "foreign_worker": "Indicador de trabajador extranjero"
    },
    "variables_no_presentes_en_data_oficial": [
        "score_buro",
        "ingreso_mensual",
        "dias_mora_prev",
        "ratio_endeudamiento",
        "tipo_empleo",
        "zona_geografica",
        "canal_captacion"
    ],
    
    # --- Anti-leakage ---
    "leakage_cols_conocidas": ["target"],
    "leakage_cols_sospechosas": [],
    "regla_anti_leakage": "No aplicar imputación, encoding, escalado, WOE ni target encoding antes del split",
    
    # --- Excelencia mínima esperada ---
    "umbrales_excelencia": {
        "roc_auc_minimo": 0.75,
        "ks_minimo": 0.30,
        "gini_minimo": 0.50,
        "overfitting_gap_maximo": 0.05
    },
    
    # --- Feature builder ---
    "feature_builder_path": "src/feature_builder.py",
    
    # --- Supuestos marcados ---
    "supuestos": [
        "[SUPUESTO] Costo operacional de evaluación manual en banda media: no provisto por el caso",
        "[SUPUESTO] Factor exposición banda media = 50% de línea completa",
        "[SUPUESTO] Pérdida promedio por default = $3,000 USD",
        "[SUPUESTO] Ganancia neta por buen pagador = $450 USD",
        "[SUPUESTO] Costo de rechazo erróneo = $150 USD",
        "[DATO] Train oficial: 800 filas, 564 good y 236 bad; tasa default = 29.5%",
        "[DATO] Test oficial: 200 filas, sin target, con columna Probabilidad vacía"
    ],
    
    "status": "READY",
    "version": "1.0",
    "timestamp": "2026-05-23T09:08:52-05:00"
}

# Guardar case_config.json
output_path = PROJECT_ROOT / "reports" / "case_config.json"
output_path.parent.mkdir(parents=True, exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(case_config, f, indent=2, ensure_ascii=False)

print("=" * 60)
print("✅ FASE 0 COMPLETADA — case_config.json generado")
print("=" * 60)
print(f"\n📌 Target: {case_config['target_col']}")
print(f"📌 ID: {case_config['id_cols']}")
print(f"📌 Métrica jurado: {case_config['metrica_jurado']}")
print(f"📌 Validación: {case_config['validation_strategy']}")
print(f"📌 Train: {case_config['data_train_path']}")
print(f"📌 Test: {case_config['data_test_path']}")
print(f"📌 Submission: {case_config['submission_cols']}")
print(f"\n💰 Matriz Económica:")
for k, v in case_config['matriz_economica'].items():
    if k != 'nota':
        print(f"   {k}: {v}")
print(f"\n🚨 Supuestos cargados: {len(case_config['supuestos'])}")
print(f"\n📄 Guardado en: {output_path}")
