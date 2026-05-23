# Herramienta de Scoring Crediticio

## Objetivo

Esta herramienta responde al requerimiento oficial del caso: ingresar caracteristicas de un solicitante, procesarlas con un modelo predictivo y retornar una estimacion de `prob_default` para decidir si el perfil es adecuado dentro de la politica de riesgo.

## Flujo ejecutable

1. Ejecutar el orquestador final:

```bash
python src/flujo_orquestador_final.py
```

2. Probar scoring individual:

```bash
python src/herramienta_scoring.py --input solicitud_ejemplo_scoring.json
```

3. Probar scoring batch:

```bash
python src/herramienta_scoring.py --input dataInicial/dataset_credito-test.xlsx --output reports/scoring_batch_test.csv
```

## Salida esperada

| Campo | Descripcion |
|---|---|
| `id_cliente` | ID de la solicitud evaluada |
| `prob_default` | Probabilidad estimada de incumplimiento |
| `banda_riesgo` | Bajo, Medio o Alto |
| `decision_politica` | Aprobar, condicionar o rechazar |
| `factores_alerta` | Lectura breve de drivers de negocio |

## Politica de decision

La politica se toma desde `models/scoring_tool.joblib`:

- Bajo riesgo: aprobar linea completa.
- Riesgo medio: condicionar al 50% o enviar a revision manual.
- Alto riesgo: rechazar o exigir mitigantes.

## Artefactos generados

- `models/scoring_tool.joblib`
- `reports/scoring_tool_report.json`
- `reports/model_comparison_orquestador.csv`
- `reports/threshold_analysis_orquestador.csv`
- `reports/politica_3_bandas_orquestador.csv`
- `submission.csv`

## Nota auditora

El flujo no usa variables que no existen en el Excel oficial, como `score_buro`, `ingreso_mensual`, `zona_geografica` o `canal_captacion`. Esas variables quedan solo como recomendacion futura para una implementacion bancaria real.
