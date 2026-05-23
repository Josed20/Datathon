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
    "target_descripcion": "1 = Default (mora >90 días), 0 = Al día / Pagador puntual",
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
        "id_cliente": "ID único del cliente — excluir del entrenamiento",
        "default_90d": "TARGET: mora >90 días (0=pagador, 1=default)",
        "edad": "Edad del solicitante — validar negativos/outliers",
        "ingreso_mensual": "Ingreso neto declarado — nulos = informalidad/sin doc",
        "score_buro": "Score historial crediticio externo — NULOS = SIN HISTORIAL FORMAL",
        "dias_mora_prev": "Días máximos de mora previa — NULOS = SIN DEUDAS/ATRASOS PREVIOS",
        "ratio_endeudamiento": "Deuda total / Ingresos — crear versión safe y capeada",
        "tipo_empleo": "Relación laboral: Dependiente/Independiente",
        "zona_geografica": "Lima, Norte, Sur, Centro, Oriente",
        "canal_captacion": "Presencial, App, Web, Asesor"
    },
    
    # --- Anti-leakage ---
    "leakage_cols_conocidas": [],
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
        "[SUPUESTO] Periodo de datos: 2022-2024, sujeto a confirmación en datos reales",
        "[SUPUESTO] Tasa de default estimada ~22% en train según documentación previa",
        "[SUPUESTO] Costo operacional de evaluación manual en banda media: no provisto por el caso",
        "[SUPUESTO] Factor exposición banda media = 50% de línea completa",
        "[SUPUESTO] Pérdida promedio por default = $3,000 USD",
        "[SUPUESTO] Ganancia neta por buen pagador = $450 USD",
        "[SUPUESTO] Costo de rechazo erróneo = $150 USD"
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
