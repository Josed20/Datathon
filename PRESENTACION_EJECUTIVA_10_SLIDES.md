# Presentación Ejecutiva — 10 Slides Máximo

## Slide 1 — FinanCrece: Score de Riesgo de Crédito

**Mensaje:** construimos un modelo de probabilidad de default para segmentar clientes y proteger rentabilidad.

Incluir:
- Datathon ESAN 2026.
- Equipo.
- Objetivo: predecir `prob_default` y proponer política de 3 bandas.

## Slide 2 — Problema de negocio

**Mensaje:** la mora erosiona rentabilidad; el score permite decidir antes de desembolsar.

Incluir:
- Mora sube de 4.2% a 7.8%.
- Decisión bancaria: aprobar, condicionar o rechazar.
- Métrica de negocio: ROI neto, no solo accuracy.

## Slide 3 — Datos oficiales y target

**Mensaje:** modelamos sobre datos oficiales sin inventar variables.

Incluir:
- Train: 800 clientes, 22 columnas.
- Test: 200 clientes, 23 columnas.
- Target raw: `target` (`good`/`bad`).
- Target canónico: `default_90d`, default rate 29.5%.
- Submission: `id_cliente`, `prob_default`.

## Slide 4 — Lecturas clave del EDA

**Mensaje:** las variables financieras sí separan riesgo.

Incluir:
- `checking_status <0`: default rate 47.4%.
- `checking_status no checking`: default rate 10.9%.
- `credit_history no credits/all paid`: default rate 65.6%.
- `savings_status <100`: default rate 35.3%.
- `housing rent/free`: mayor riesgo que vivienda propia.

## Slide 5 — Feature engineering crediticio

**Mensaje:** transformamos variables en señales bancarias reproducibles.

Incluir:
- Carga financiera: `credit_amount * duration`.
- Cuota estimada: `credit_amount / duration`.
- Ordinales de riesgo: checking, historial, ahorros, empleo.
- Interacciones: cuenta negativa + monto alto, sin reservas, riesgo combinado.
- Regla anti-leakage: mismas transformaciones fila a fila para train y test.

## Slide 6 — Estrategia de modelado

**Mensaje:** comparamos modelos y priorizamos discriminación, estabilidad y negocio.

Incluir:
- Baseline, regresión logística, Random Forest, boosting.
- Campeón: `LGB_regularizado`.
- Split estratificado por ausencia de fecha confiable.
- Métricas: AUC, Gini, KS, Brier, PR-AUC, Lift@10.

## Slide 7 — Resultados técnicos

**Mensaje:** el modelo logra separación competitiva para scoring.

Incluir:
- ROC-AUC validación: 0.8326.
- Gini: 0.6652.
- KS: 0.6334.
- Brier: 0.1565.
- Lift@10: 2.34.
- Nota honesta: test interno AUC 0.7155; se controla con regularización y bandas, no con sobrepromesa.

## Slide 8 — Política de 3 bandas

**Mensaje:** la probabilidad se convierte en acción de negocio.

| Banda | Probabilidad | Default observado | Decisión |
|---|---:|---:|---|
| Bajo | `< 0.15` | 2.38% | Aprobar línea completa |
| Medio | `0.15 - 0.40` | 17.02% | Condicionar 50% |
| Alto | `>= 0.40` | 53.52% | Rechazar/evaluar manual |

## Slide 9 — Impacto financiero

**Mensaje:** la política reduce pérdidas esperadas y preserva buenos clientes.

Incluir:
- Matriz económica: buen aprobado +USD 450; buen rechazado -USD 150; default aprobado -USD 3,000.
- Ahorro estimado vs base: USD 97,425.
- ROI vs base: +107.15%.
- Marcar valores como simulación bajo supuestos documentados.

## Slide 10 — Recomendación final

**Mensaje:** FinanCrece debe operar con score, bandas y monitoreo.

Incluir:
- Implementar score como motor de originación.
- Banda media a evaluación reforzada o línea reducida.
- Monitorear drift, calibración y default real mensual.
- Siguiente mejora: integrar ingresos, buró real, región, canal y macroeconomía.
- Cierre: modelo interpretable + política accionable + ROI medible.
