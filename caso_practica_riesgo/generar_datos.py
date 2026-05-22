import os
import numpy as np
import pandas as pd
from pathlib import Path

# Configurar semilla de aleatoriedad para reproducibilidad
np.random.seed(42)

# Crear directorios
output_dir = Path("c:/Cursos/Datathon/caso_practica_riesgo")
data_dir = output_dir / "dataInicial"
data_dir.mkdir(parents=True, exist_ok=True)

print(f"Creando caso de práctica en: {output_dir}")

# --- 1. GENERAR DATASET DE ENTRENAMIENTO (15,000 clientes) ---
n_train = 15000

# Variables base
ids_train = [f"CLI_{i:06d}" for i in range(1, n_train + 1)]

# Fechas de solicitud distribuidas en 12 meses (2025-01-01 a 2025-12-31)
start_date = pd.to_datetime("2025-01-01")
end_date = pd.to_datetime("2025-12-31")
days_range = (end_date - start_date).days
fechas_train = start_date + pd.to_timedelta(np.random.randint(0, days_range, size=n_train), unit="D")

# Edad (con algunos valores anómalos, ej. valores negativos o extremadamente altos)
edad = np.random.normal(41, 11, size=n_train).astype(int)
edad = np.clip(edad, 18, 85)
# Introducir 15 valores anómalos de edad negativa para auditoría de calidad
anomalous_edad_idx = np.random.choice(n_train, 15, replace=False)
edad[anomalous_edad_idx] = -999

# Ingresos mensuales (con nulos y outliers gigantes de millonarios)
ingresos = np.random.exponential(scale=3500, size=n_train) + 1025 # salario mínimo
# Añadir outliers extremos
outlier_income_idx = np.random.choice(n_train, 50, replace=False)
ingresos[outlier_income_idx] = ingresos[outlier_income_idx] * 12
# Introducir 8% de valores nulos para imputación
null_income_idx = np.random.choice(n_train, int(n_train * 0.08), replace=False)
ingresos_with_nulls = ingresos.copy()
ingresos_with_nulls[null_income_idx] = np.nan

# Categorías
tipo_vivienda_opts = ["ALQUILER", "HIPOTECA", "PROPIA"]
tipo_vivienda = np.random.choice(tipo_vivienda_opts, size=n_train, p=[0.35, 0.40, 0.25])

situacion_laboral_opts = ["DEPENDIENTE", "INDEPENDIENTE", "DESEMPLEADO"]
situacion_laboral = np.random.choice(situacion_laboral_opts, size=n_train, p=[0.70, 0.22, 0.08])

nivel_educativo_opts = ["SECUNDARIA", "UNIVERSITARIO", "POSGRADO"]
nivel_educativo = np.random.choice(nivel_educativo_opts, size=n_train, p=[0.30, 0.55, 0.15])

estado_civil_opts = ["SOLTERO", "CASADO", "DIVORCIADO"]
estado_civil = np.random.choice(estado_civil_opts, size=n_train, p=[0.45, 0.40, 0.15])

# Comportamiento crediticio
linea_credito = np.random.exponential(scale=12000, size=n_train) + 1500
saldo_deudor = linea_credito * np.random.beta(a=1.5, b=3, size=n_train)
# Asegurar que saldo deudor no supere la línea excepto en sobregiros
overdraft_idx = np.random.choice(n_train, int(n_train * 0.03), replace=False)
saldo_deudor[overdraft_idx] = saldo_deudor[overdraft_idx] * 1.15

utilizacion = saldo_deudor / linea_credito

# Historial de atrasos (valores enteros altamente correlacionados con default)
num_atrasos_30 = np.random.poisson(lam=0.2, size=n_train)
num_atrasos_60 = np.random.poisson(lam=0.07, size=n_train)
num_atrasos_90 = np.random.poisson(lam=0.03, size=n_train)

# Consultas a central de riesgo en últimos 6 meses (con nulos)
consultas = np.random.poisson(lam=1.1, size=n_train)
null_consultas_idx = np.random.choice(n_train, int(n_train * 0.04), replace=False)
consultas_with_nulls = consultas.copy().astype(float)
consultas_with_nulls[null_consultas_idx] = np.nan

# Generar la probabilidad del default basada en una función logística real + ruido
# Esto garantiza que el problema sea resoluble pero requiera feature engineering
z = (
    -3.2
    + 3.5 * utilizacion
    + 1.8 * num_atrasos_90
    + 1.1 * num_atrasos_60
    + 0.6 * num_atrasos_30
    + 0.4 * (consultas)
    - 0.02 * ((edad - 40) / 10)
    - 0.5 * (ingresos / 5000)
    + 0.8 * (situacion_laboral == "DESEMPLEADO")
    + 0.3 * (tipo_vivienda == "ALQUILER")
)
# Agregar ruido
z += np.random.normal(0, 0.6, size=n_train)
prob_default = 1 / (1 + np.exp(-z))
default = (prob_default > np.random.uniform(0, 1, size=n_train)).astype(int)

# Crear DataFrame de Entrenamiento
df_train = pd.DataFrame({
    "ID_CLIENTE": ids_train,
    "FECHA_SOLICITUD": fechas_train.strftime("%Y-%m-%d"),
    "EDAD": edad,
    "ESTADO_CIVIL": estado_civil,
    "NIVEL_EDUCATIVO": nivel_educativo,
    "SITUACION_LABORAL": situacion_laboral,
    "TIPO_VIVIENDA": tipo_vivienda,
    "INGRESOS_MENSUALES": ingresos_with_nulls,
    "LINEA_CREDITO_TOTAL": np.round(linea_credito, 2),
    "SALDO_DEUDOR_TOTAL": np.round(saldo_deudor, 2),
    "NUM_ATRASOS_30_59_DIAS": num_atrasos_30,
    "NUM_ATRASOS_60_89_DIAS": num_atrasos_60,
    "NUM_ATRASOS_90_MAS_DIAS": num_atrasos_90,
    "NUM_CONSULTAS_CENTRAL": consultas_with_nulls,
    "DEFAULT": default
})


# --- 2. GENERAR DATASET DE PRUEBA (5,000 clientes, SIN TARGET) ---
n_test = 5000
ids_test = [f"CLI_{i:06d}" for i in range(n_train + 1, n_train + n_test + 1)]

# Fechas en el primer trimestre de 2026 (después de train, ideal para validación temporal)
start_date_test = pd.to_datetime("2026-01-01")
end_date_test = pd.to_datetime("2026-03-31")
days_range_test = (end_date_test - start_date_test).days
fechas_test = start_date_test + pd.to_timedelta(np.random.randint(0, days_range_test, size=n_test), unit="D")

# Repetir generación de variables para test
edad_test = np.random.normal(41.2, 10.8, size=n_test).astype(int)
edad_test = np.clip(edad_test, 18, 85)
# Pocos anómalos de edad
anomalous_edad_test_idx = np.random.choice(n_test, 3, replace=False)
edad_test[anomalous_edad_test_idx] = -999

ingresos_test = np.random.exponential(scale=3600, size=n_test) + 1025
outlier_income_test_idx = np.random.choice(n_test, 15, replace=False)
ingresos_test[outlier_income_test_idx] = ingresos_test[outlier_income_test_idx] * 11
null_income_test_idx = np.random.choice(n_test, int(n_test * 0.08), replace=False)
ingresos_test_with_nulls = ingresos_test.copy()
ingresos_test_with_nulls[null_income_test_idx] = np.nan

tipo_vivienda_test = np.random.choice(tipo_vivienda_opts, size=n_test, p=[0.35, 0.40, 0.25])
situacion_laboral_test = np.random.choice(situacion_laboral_opts, size=n_test, p=[0.70, 0.22, 0.08])
nivel_educativo_test = np.random.choice(nivel_educativo_opts, size=n_test, p=[0.30, 0.55, 0.15])
estado_civil_test = np.random.choice(estado_civil_opts, size=n_test, p=[0.45, 0.40, 0.15])

linea_credito_test = np.random.exponential(scale=12200, size=n_test) + 1500
saldo_deudor_test = linea_credito_test * np.random.beta(a=1.5, b=3, size=n_test)
overdraft_test_idx = np.random.choice(n_test, int(n_test * 0.03), replace=False)
saldo_deudor_test[overdraft_test_idx] = saldo_deudor_test[overdraft_test_idx] * 1.15

num_atrasos_30_test = np.random.poisson(lam=0.19, size=n_test)
num_atrasos_60_test = np.random.poisson(lam=0.065, size=n_test)
num_atrasos_90_test = np.random.poisson(lam=0.028, size=n_test)

consultas_test = np.random.poisson(lam=1.05, size=n_test)
null_consultas_test_idx = np.random.choice(n_test, int(n_test * 0.04), replace=False)
consultas_test_with_nulls = consultas_test.copy().astype(float)
consultas_test_with_nulls[null_consultas_test_idx] = np.nan

# Crear DataFrame de Test (sin columna DEFAULT)
df_test = pd.DataFrame({
    "ID_CLIENTE": ids_test,
    "FECHA_SOLICITUD": fechas_test.strftime("%Y-%m-%d"),
    "EDAD": edad_test,
    "ESTADO_CIVIL": estado_civil_test,
    "NIVEL_EDUCATIVO": nivel_educativo_test,
    "SITUACION_LABORAL": situacion_laboral_test,
    "TIPO_VIVIENDA": tipo_vivienda_test,
    "INGRESOS_MENSUALES": ingresos_test_with_nulls,
    "LINEA_CREDITO_TOTAL": np.round(linea_credito_test, 2),
    "SALDO_DEUDOR_TOTAL": np.round(saldo_deudor_test, 2),
    "NUM_ATRASOS_30_59_DIAS": num_atrasos_30_test,
    "NUM_ATRASOS_60_89_DIAS": num_atrasos_60_test,
    "NUM_ATRASOS_90_MAS_DIAS": num_atrasos_90_test,
    "NUM_CONSULTAS_CENTRAL": consultas_test_with_nulls
})


# --- 3. GUARDAR DATASETS EN FORMATO CSV Y EXCEL ---
train_csv_path = data_dir / "clientes_entrenamiento.csv"
test_csv_path = data_dir / "clientes_prueba.csv"

df_train.to_csv(train_csv_path, index=False)
df_test.to_csv(test_csv_path, index=False)

# Guardar entrenamiento también en Excel para simular diversidad de formatos
df_train.to_excel(data_dir / "clientes_entrenamiento.xlsx", index=False)

print(f"Archivos guardados en: {data_dir}")
print(f"Entrenamiento: {df_train.shape[0]} filas, {df_train.shape[1]} columnas. Default rate: {df_train['DEFAULT'].mean()*100:.2f}%")
print(f"Prueba: {df_test.shape[0]} filas, {df_test.shape[1]} columnas (sin TARGET).")
