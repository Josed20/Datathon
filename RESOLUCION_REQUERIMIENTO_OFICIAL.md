# Resolución del Requerimiento Oficial

## Requerimiento

El caso pide una herramienta que permita ingresar características específicas de un solicitante, procesarlas mediante un modelo predictivo y retornar una estimación confiable de la probabilidad de incumplimiento o default para decidir si el perfil es adecuado dentro de la política de riesgo de la institución financiera.

## Solución implementada

Se implementó un flujo final en `src/flujo_orquestador_final.py` y una herramienta de scoring en `src/herramienta_scoring.py`.

La solución cumple el requerimiento así:

| Requerimiento oficial | Implementación |
|---|---|
| Ingresar características específicas | JSON, CSV o Excel con las variables oficiales del solicitante |
| Procesar con modelo predictivo | Pipeline sklearn con imputación, escalado, one-hot encoding y modelo campeón |
| Retornar probabilidad de default | Campo `prob_default` entre 0 y 1 |
| Determinar aprobación del préstamo | Campo `banda_riesgo` y `decision_politica` |
| Respetar política de riesgo | Política de 3 bandas optimizada en validación |

## Modelo campeón

Modelo seleccionado: `LogReg_balanced_C01`.

Se eligió porque ofrece el mejor balance auditor entre:

- AUC competitivo.
- Menor sobreajuste que modelos de árboles más agresivos.
- Probabilidades más defendibles para scoring.
- Interpretabilidad bancaria.
- Portabilidad con dependencias disponibles.

## Métricas de validación

| Métrica | Valor |
|---|---:|
| ROC-AUC | 0.8021 |
| Gini | 0.6042 |
| KS | 0.5272 |
| Brier | 0.1704 |
| PR-AUC | 0.6056 |
| Lift@10 | 2.13 |
| Gap train-val | 0.0626 |

## Política de riesgo

| Banda | Probabilidad | Default observado | Decisión |
|---|---:|---:|---|
| Bajo | `< 0.30` | 7.04% | Aprobar línea completa |
| Medio | `0.30 - 0.36` | 11.11% | Condicionar al 50% o revisión manual |
| Alto | `>= 0.36` | 51.25% | Rechazar o exigir mitigantes |

Threshold binario óptimo para ROI: `0.36`.

Ahorro incremental estimado vs base: USD 99,600.

## Comandos de uso

Entrenar y generar herramienta:

```bash
python src/flujo_orquestador_final.py
```

Scoring individual:

```bash
python src/herramienta_scoring.py --input solicitud_ejemplo_scoring.json
```

Scoring batch:

```bash
python src/herramienta_scoring.py --input dataInicial/dataset_credito-test.xlsx --output reports/scoring_batch_test.csv
```

## Artefactos generados

- `models/scoring_tool.joblib`
- `reports/scoring_tool_report.json`
- `reports/model_comparison_orquestador.csv`
- `reports/threshold_analysis_orquestador.csv`
- `reports/politica_3_bandas_orquestador.csv`
- `reports/scoring_batch_test.csv`
- `submission.csv`

## Nota metodológica

La solución usa teoría de scoring crediticio aplicada: separación anti-leakage, probabilidad de default, métricas Gini/KS/Brier/Lift, evaluación de ROI y bandas de decisión. Las variables no presentes en los Excel oficiales, como buró externo, ingreso mensual o zona geográfica, no se usan en el modelo y quedan como recomendación futura.
