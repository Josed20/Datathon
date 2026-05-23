# Auditoría Senior del Repositorio — Caso Datathon ESAN 2026

## Veredicto ejecutivo

El repositorio ya tiene una base competitiva: datos procesados, modelo entrenado, simulación de bandas, artefactos en `reports/`, modelo serializado y `submission.csv`. La principal debilidad detectada no era de potencia técnica, sino de coherencia: parte de la documentación seguía describiendo un caso genérico con `score_buro`, `ingreso_mensual`, `ratio_endeudamiento` y decenas de miles de filas, mientras los archivos oficiales corresponden a un German Credit adaptado con 800 filas de train y 200 de test.

La auditoría corrige esa contradicción y deja el flujo listo para trabajar en 3 horas sin que EDA, modelado y presentación se contradigan.

## Qué pide el caso oficial

- Problema: scoring de crédito para FinanCrece S.A. con foco en mora/default.
- Train oficial: `dataInicial/dataset_credito-train.xlsx`, 800 filas, 22 columnas.
- Test oficial: `dataInicial/dataset_credito-test.xlsx`, 200 filas, 23 columnas.
- Target original: `target`, con valores `good` y `bad`.
- Target canónico del repositorio: `default_90d`, donde `good=0` y `bad=1`.
- Tasa de default en train: 236/800 = 29.5%.
- Submission esperado: `submission.csv` con `id_cliente` y `prob_default`.
- Entregables operativos: notebook limpio, submission y presentación ejecutiva de máximo 10 slides.

## Hallazgos críticos y correcciones aplicadas

| Severidad | Hallazgo | Riesgo | Corrección aplicada |
|---|---|---|---|
| Alta | El Orquestador hablaba de 40k/10k filas y variables inexistentes. | El equipo podía construir EDA/modelos sobre columnas falsas. | `ORQUESTADOR_DATATHON.md` quedó alineado a los Excel oficiales. |
| Alta | El EDA formal asumía que `default_90d` ya existía. | Error o fuga si se usaba `target` como predictor. | `src/fase1_eda.py` ahora mapea `target` a `default_90d` y excluye `target`. |
| Alta | Faltaba `reports/eda_handoff.json`, aunque el contrato lo exige. | El Doc 2 no tenía entrada autoritativa del EDA. | Se creó `reports/eda_handoff.json` con rutas, target, estrategia y warnings. |
| Media | El EDA graficaba variables genéricas no presentes. | Figuras vacías o poco útiles para la defensa. | Se reemplazó por variables reales: `duration`, `credit_amount`, `installment_commitment`, `age`, etc. |
| Media | Variables con dtype `str` quedaban clasificadas como numéricas. | EDA bivariado y narrativa podían quedar distorsionados. | Se actualizó la regla de clasificación y `reports/clasificacion_columnas.csv`. |
| Media | La validación temporal aparecía como alternativa fuerte. | Simular tiempo sin fecha genera falsa robustez. | Se fija `stratified_split` porque no existe columna temporal confiable. |
| Media | El reporte de calidad decía que el target no existía. | Contradicción directa contra el pipeline. | `reports/data_quality_report.json` quedó corregido con distribución real. |

## Estructura actual recomendada

| Carpeta/archivo | Rol correcto |
|---|---|
| `ORQUESTADOR_DATATHON.md` | Fuente de verdad del flujo y de los supuestos del caso. |
| `EDA_Guia_Datathon_Banca.md` | Guía técnica de EDA, ahora con target raw y rutas oficiales. |
| `Modelado_Validacion_Datathon_Banca.md` | Guía de modelado, métricas, calibración, umbrales, ROI y explicación. |
| `src/pipeline_completo.py` | Ruta ejecutable principal para rehacer el pipeline completo. |
| `src/feature_builder.py` | Ingeniería reproducible para train/test. |
| `reports/case_config.json` | Configuración autoritativa del caso. |
| `reports/eda_handoff.json` | Contrato listo para que modelado consuma el EDA. |
| `models/model_metadata.json` | Métricas y política final del modelo regularizado. |
| `submission.csv` | Entregable final de predicción. |

## Métricas ya disponibles

Modelo regularizado actual: `LGB_regularizado`.

| Métrica | Validación |
|---|---:|
| ROC-AUC | 0.8326 |
| Gini | 0.6652 |
| KS | 0.6334 |
| Brier | 0.1565 |
| PR-AUC | 0.6677 |
| Lift@10 | 2.34 |
| Gap train-val | 0.0941 |

Riesgo técnico: el test interno cae a AUC 0.7155, con gap val-test 0.1171. Para la presentación, vender el modelo como competitivo y útil, no como perfecto. La defensa debe enfatizar regularización, bandas, calibración revisada y control de sobreajuste.

## Política de 3 bandas vigente

| Banda | Umbral | % clientes val | Default observado | Decisión |
|---|---:|---:|---:|---|
| Bajo riesgo | `< 0.15` | 26.2% | 2.38% | Aprobar línea completa |
| Riesgo medio | `0.15 - 0.40` | 29.4% | 17.02% | Condicionar al 50% |
| Alto riesgo | `>= 0.40` | 44.4% | 53.52% | Rechazar o enviar a evaluación manual |

Ahorro estimado vs política base: USD 97,425. Este valor debe presentarse como simulación con matriz económica del caso/supuestos.

## Plan de 3 horas recomendado

| Minutos | Responsable | Acción |
|---:|---|---|
| 0-15 | Técnico | Confirmar archivos, target, shape, tasa default y submission. |
| 15-45 | Técnico + Financista | EDA corto: target, variables top, default rates, calidad y leakage. |
| 45-100 | Técnico | Reejecutar pipeline, revisar métricas, calibración y bandas. |
| 100-125 | Financista | ROI, lectura de bandas, recomendación de política. |
| 125-145 | Ingeniera ambiental | Enriquecer explicación externa: contexto macro, inclusión financiera y límites de datos. |
| 145-170 | Todos | Notebook final + `submission.csv` + validación de columnas. |
| 170-180 | Todos | Ensayo express de presentación y defensa de supuestos. |

## Riesgos residuales

- Falta convertir o confirmar el notebook final en formato `.ipynb` si el jurado no acepta `.py`.
- Falta construir el PPT/PPTX final; existe la lógica para 10 slides, pero debe materializarse.
- El entorno actual de shell no tiene todas las librerías de ML disponibles, por lo que la auditoría revisó artefactos existentes y consistencia de código, pero no reejecutó el pipeline completo.
- No hay variables macroeconómicas, geográficas ni de ingreso en los Excel. Se pueden discutir como limitación y recomendación futura, no como insumo del modelo.

## Conclusión auditora

El sistema queda coherente y orientado al caso oficial. La ruta ganadora no es prometer un score perfecto, sino defender un modelo robusto, interpretable, con control de leakage, métricas de scoring crediticio y una política de decisión conectada a ROI bancario.
