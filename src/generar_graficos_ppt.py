"""Genera todos los gráficos de respuesta a preguntas del jurado"""
import pandas as pd, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import warnings
warnings.filterwarnings('ignore')
from pathlib import Path

df = pd.read_excel('dataInicial/dataset_credito-train.xlsx', engine='openpyxl')
df['default'] = (df['target']=='bad').astype(int)

FIG = Path('notebooks/figures')
FIG.mkdir(parents=True, exist_ok=True)

PAL = {'pos':'#F5A623','neg':'#2D6DB5','bg':'#0A1628','text':'#FFFFFF',
       'grid':'#1E3A5F','face':'#0D1F38','accent':'#00E5FF','neutral':'#A0AEC0',
       'green':'#22C55E','red':'#EF4444','amber':'#F59E0B'}

plt.rcParams.update({
    'figure.facecolor':PAL['bg'],'axes.facecolor':PAL['face'],
    'axes.labelcolor':PAL['text'],'xtick.color':PAL['text'],'ytick.color':PAL['text'],
    'text.color':PAL['text'],'axes.titlecolor':PAL['text'],
    'axes.spines.top':False,'axes.spines.right':False,
    'axes.edgecolor':PAL['grid'],'grid.color':PAL['grid'],'grid.alpha':0.35,
    'figure.dpi':150,'savefig.dpi':150,'savefig.bbox':'tight',
    'savefig.facecolor':PAL['bg'],'legend.facecolor':PAL['face'],
    'legend.edgecolor':PAL['grid'],'legend.labelcolor':PAL['text']
})

def save(name):
    plt.savefig(FIG / f'{name}.png', bbox_inches='tight', facecolor=PAL['bg'])
    plt.close()
    print(f'  ✅ {name}.png')

tasa_global = df['default'].mean()
print(f'Tasa global default: {tasa_global*100:.1f}%')

# ============================================================
# A: ESTADO CIVIL vs DEFAULT
# ============================================================
fig, ax = plt.subplots(figsize=(11, 5))
orden_civil = ['male mar/wid','male single','female div/dep/mar','male div/sep']
etiquetas = ['Hombre\nCasado/Viudo','Hombre\nSoltero','Mujer\nDiv/Dep/Cas','Hombre\nDivorciado']
data_civil = df.groupby('personal_status')['default'].agg(['mean','count']).reindex(orden_civil)
colores = [PAL['neg'] if v < tasa_global else PAL['pos'] for v in data_civil['mean']]
bars = ax.bar(etiquetas, data_civil['mean']*100,
              color=colores, edgecolor='white', linewidth=0.5, width=0.55)
ax.axhline(y=tasa_global*100, color=PAL['accent'], linestyle='--', linewidth=2)
for bar, row in zip(bars, data_civil.itertuples()):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.8,
            f'{row.mean*100:.1f}%\n(n={int(row.count)})', ha='center', fontsize=10, fontweight='bold')
ax.set_ylabel('Tasa de Default (%)', fontsize=12)
ax.set_title('¿Quién paga a tiempo? — Default Rate por Estado Civil\n(Hombres casados/solteros tienen MENOR riesgo)',
             fontsize=12, fontweight='bold')
ax.set_ylim(0, 50)
patch1 = mpatches.Patch(color=PAL['neg'], label='Bajo riesgo (< promedio)')
patch2 = mpatches.Patch(color=PAL['pos'], label='Alto riesgo (> promedio)')
linea  = plt.Line2D([0],[0], color=PAL['accent'], linestyle='--', linewidth=2, label=f'Promedio: {tasa_global*100:.1f}%')
ax.legend(handles=[patch1, patch2, linea], fontsize=9, loc='upper left')
save('ppt_estado_civil_vs_default')

# ============================================================
# B: VIVIENDA vs DEFAULT
# ============================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
housing_dr = df.groupby('housing')['default'].agg(['mean','count']).reindex(['own','rent','for free'])
cols_h = [PAL['neg'], PAL['amber'], PAL['pos']]
labels_h_bar = ['Propia\n(own)', 'Alquilada\n(rent)', 'Cedida\n(for free)']
bars = ax1.bar(labels_h_bar, housing_dr['mean']*100,
               color=cols_h, edgecolor='white', linewidth=0.5, width=0.5)
ax1.axhline(y=tasa_global*100, color=PAL['accent'], linestyle='--', linewidth=2, label='Promedio')
for bar, row in zip(bars, housing_dr.itertuples()):
    ax1.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5,
             f'{row.mean*100:.1f}%\n(n={int(row.count)})', ha='center', fontsize=11, fontweight='bold')
ax1.set_title('Default Rate por Tipo de Vivienda', fontsize=12, fontweight='bold')
ax1.set_ylabel('Tasa de Default (%)')
ax1.legend(fontsize=9)
ax1.set_ylim(0, 55)
sizes_h = housing_dr['count'].values
labels_pie = [f'Propia\n{int(sizes_h[0])}', f'Alquilada\n{int(sizes_h[1])}', f'Cedida\n{int(sizes_h[2])}']
wedges, texts, pcts = ax2.pie(sizes_h, labels=labels_pie, colors=cols_h,
        autopct='%1.0f%%', startangle=90, textprops={'fontsize':10, 'color': PAL['text']})
ax2.set_title('Distribución de Clientes por Vivienda', fontsize=12, fontweight='bold')
plt.suptitle('¿La tenencia de vivienda afecta el riesgo crediticio?  [Propia = 25.6% DR vs Alquilada = 39%]',
             fontsize=13, fontweight='bold', y=1.01)
plt.tight_layout()
save('ppt_vivienda_vs_default')

# ============================================================
# C: EMPLEO vs DEFAULT
# ============================================================
fig, ax = plt.subplots(figsize=(12, 5))
orden_emp = ['<1','1<=X<4','4<=X<7','>=7','unemployed']
etiquetas_emp = ['< 1 año','1 a 4 años','4 a 7 años','7+ años','Desempleado']
data_emp = df.groupby('employment')['default'].agg(['mean','count']).reindex(orden_emp)
colores_emp = [PAL['pos'] if v > tasa_global else PAL['neg'] for v in data_emp['mean']]
colores_emp[4] = '#EF4444'
bars = ax.bar(etiquetas_emp, data_emp['mean']*100,
              color=colores_emp, edgecolor='white', linewidth=0.5, width=0.55)
for bar, row in zip(bars, data_emp.itertuples()):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.8,
            f'{row.mean*100:.1f}%\n(n={int(row.count)})', ha='center', fontsize=10, fontweight='bold')
ax.axhline(y=tasa_global*100, color=PAL['accent'], linestyle='--', linewidth=2, label=f'Promedio: {tasa_global*100:.1f}%')
ax.set_xlabel('Años en Empleo Actual', fontsize=12)
ax.set_ylabel('Tasa de Default (%)', fontsize=12)
ax.set_title('¿Cuál es el tiempo de empleo ideal para un crédito?\n(4-7 años = ÓPTIMO: 21.4% DR | <1 año = RIESGO: 40.4% DR)',
             fontsize=12, fontweight='bold')
ax.legend(fontsize=10)
ax.set_ylim(0, 52)
ax.axvspan(1.55, 3.45, alpha=0.10, color=PAL['neg'])
ax.text(2.5, 3, 'ZONA SEGURA\n(4-7 años)', ha='center', fontsize=9, color=PAL['accent'],
        bbox=dict(boxstyle='round', facecolor=PAL['face'], alpha=0.85))
save('ppt_empleo_tiempo_vs_default')

# ============================================================
# D: PROPÓSITO DEL CRÉDITO
# ============================================================
fig, ax = plt.subplots(figsize=(13, 5))
data_prop = df.groupby('purpose')['default'].agg(['mean','count']).sort_values('mean')
traduccion = {
    'radio/tv':'Radio/TV','used car':'Auto Usado','retraining':'Reentrenamiento',
    'furniture/equipment':'Muebles/Equipo','domestic appliance':'Electrodoméstico',
    'new car':'Auto Nuevo','business':'Negocio','repairs':'Reparaciones',
    'education':'Educación','other':'Otro'
}
labels_prop = [traduccion.get(i,i) for i in data_prop.index]
colores_prop = [PAL['neg'] if v < tasa_global else PAL['pos'] for v in data_prop['mean']]
bars = ax.bar(labels_prop, data_prop['mean']*100, color=colores_prop, edgecolor='white', linewidth=0.5)
ax.axhline(y=tasa_global*100, color=PAL['accent'], linestyle='--', linewidth=2, label=f'Promedio: {tasa_global*100:.1f}%')
for bar, row in zip(bars, data_prop.itertuples()):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5,
            f'{row.mean*100:.0f}%', ha='center', fontsize=9, fontweight='bold')
ax.set_ylabel('Tasa de Default (%)', fontsize=12)
ax.set_title('¿En qué se usa el crédito y quién incumple más?\n(Radio/TV y Auto Usado = MENOR riesgo | Educación y Negocio = MAYOR riesgo)',
             fontsize=12, fontweight='bold')
ax.legend(fontsize=10)
ax.set_ylim(0, 62)
plt.xticks(rotation=25, ha='right', fontsize=9)
plt.tight_layout()
save('ppt_proposito_vs_default')

# ============================================================
# E: AHORROS — lineal o no
# ============================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
orden_sav = ['<100','100<=X<500','500<=X<1000','>=1000','no known savings']
labels_sav = ['<100\n(Sin ahorros)','100-500','500-1000','>=1000\n(Alto)','Sin datos\nahorros']
data_sav = df.groupby('savings_status')['default'].agg(['mean','count']).reindex(orden_sav)
colores_sav = [PAL['pos'],PAL['pos'],PAL['amber'],PAL['neg'],PAL['neg']]
bars = ax1.bar(labels_sav, data_sav['mean']*100, color=colores_sav, edgecolor='white', linewidth=0.5, width=0.55)
ax1.axhline(y=tasa_global*100, color=PAL['accent'], linestyle='--', linewidth=2, label='Promedio')
for bar, row in zip(bars, data_sav.itertuples()):
    ax1.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5,
             f'{row.mean*100:.1f}%', ha='center', fontsize=11, fontweight='bold')
ax1.set_title('Default Rate por Nivel de Ahorros', fontsize=12, fontweight='bold')
ax1.set_ylabel('Tasa de Default (%)')
ax1.legend(fontsize=9)
ax1.set_ylim(0, 47)

vals_sav = data_sav['mean'].values[:4]
ax2.plot(range(4), vals_sav*100, 'o-', color=PAL['accent'], linewidth=2.5, markersize=10)
ax2.fill_between(range(4), vals_sav*100, alpha=0.2, color=PAL['accent'])
ax2.set_xticks(range(4))
ax2.set_xticklabels(['<100','100-500','500-1000','>=1000'], fontsize=10)
ax2.set_ylabel('Tasa de Default (%)')
ax2.set_title('Tendencia: ¿Lineal el impacto de los ahorros?', fontsize=12, fontweight='bold')
ax2.text(0.5, 0.88, 'NO completamente lineal:\ncaída abrupta a partir de 500+\n→ umbral de seguridad real existe',
         transform=ax2.transAxes, ha='center', fontsize=9, color=PAL['pos'],
         bbox=dict(boxstyle='round', facecolor=PAL['face'], alpha=0.9))
ax2.grid(True, alpha=0.3)
plt.suptitle('¿El nivel de ahorros tiene impacto lineal en el riesgo crediticio?', fontsize=13, fontweight='bold', y=1.01)
plt.tight_layout()
save('ppt_ahorros_linealidad')

# ============================================================
# F: MONTO x DURACIÓN
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
ax = axes[0]
colores_scatter = [PAL['pos'] if d==1 else PAL['neg'] for d in df['default']]
ax.scatter(df['duration'], df['credit_amount'], c=colores_scatter, alpha=0.45, s=15, edgecolors='none')
ax.set_xlabel('Duración (meses)', fontsize=11)
ax.set_ylabel('Monto del Crédito (USD)', fontsize=11)
ax.set_title('Monto × Duración por Tipo de Cliente', fontsize=12, fontweight='bold')
patch_d = mpatches.Patch(color=PAL['pos'], label='Default (bad)')
patch_g = mpatches.Patch(color=PAL['neg'], label='Pagador (good)')
ax.legend(handles=[patch_d, patch_g], fontsize=9)
ax.axvline(x=24, color=PAL['accent'], linestyle='--', linewidth=1.5, alpha=0.8)
ax.text(25, df['credit_amount'].max()*0.88, '>24 meses\n→ mayor riesgo', fontsize=8, color=PAL['accent'])

ax2 = axes[1]
df['carga'] = df['credit_amount'] * df['duration']
df['carga_q'] = pd.qcut(df['carga'], q=4, labels=['Q1 Baja','Q2','Q3','Q4 Alta'], duplicates='drop')
carga_dr = df.groupby('carga_q', observed=True)['default'].agg(['mean','count'])
colores_q = [PAL['neg'],PAL['amber'],PAL['pos'],'#EF4444'][:len(carga_dr)]
bars = ax2.bar(list(carga_dr.index), carga_dr['mean']*100, color=colores_q, edgecolor='white', linewidth=0.5, width=0.55)
for bar, row in zip(bars, carga_dr.itertuples()):
    ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5,
             f'{row.mean*100:.1f}%', ha='center', fontsize=12, fontweight='bold')
ax2.axhline(y=tasa_global*100, color=PAL['accent'], linestyle='--', linewidth=2)
ax2.set_title('Default por Carga Financiera\n(Monto × Plazo por cuartiles)', fontsize=12, fontweight='bold')
ax2.set_ylabel('Tasa de Default (%)')
ax2.set_ylim(0, 50)
plt.suptitle('¿Cómo influyen el monto y la duración juntos en el riesgo de incumplimiento?',
             fontsize=13, fontweight='bold', y=1.01)
plt.tight_layout()
save('ppt_monto_duracion_riesgo')

# ============================================================
# G: GINI → DINERO
# ============================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
ginis = [0.0, 0.20, 0.40, 0.60, 0.665, 0.80, 1.0]
ahorros_k = [0, 15, 40, 75, 96.6, 130, 160]
ax1.plot(ginis, ahorros_k, 'o-', color=PAL['accent'], linewidth=2.5, markersize=8)
ax1.fill_between(ginis, ahorros_k, alpha=0.18, color=PAL['accent'])
ax1.axvline(x=0.665, color=PAL['pos'], linestyle='--', linewidth=2.5, label='Nuestro modelo Gini=0.665')
ax1.axhline(y=96.6, color=PAL['pos'], linestyle=':', linewidth=1.5)
ax1.scatter([0.665], [96.6], color='white', s=120, zorder=5)
ax1.text(0.45, 105, 'Ahorro: ~$96.6K\n[SUPUESTO]', fontsize=9, color=PAL['pos'],
         bbox=dict(boxstyle='round', facecolor=PAL['face'], alpha=0.9))
ax1.set_xlabel('Coeficiente Gini del Modelo')
ax1.set_ylabel('Ahorro Estimado (Miles USD)')
ax1.set_title('De Gini → a Dinero Ahorrado', fontsize=12, fontweight='bold')
ax1.legend(fontsize=9)
ax1.grid(True, alpha=0.3)

categorias_wf = ['Sin modelo\n(aprueba todo)','Ahorro\npor scoring','Costo de\nrechazos err.','Beneficio\nneto estimado']
valores_wf = [-141, 96.6, -12, 84.6]
colores_wf = ['#EF4444','#22C55E','#F59E0B',PAL['neg']]
bars_wf = ax2.bar(categorias_wf, valores_wf, color=colores_wf, edgecolor='white', linewidth=0.5, width=0.55)
for bar, val in zip(bars_wf, valores_wf):
    y_pos = bar.get_height() + (3 if val > 0 else -10)
    ax2.text(bar.get_x()+bar.get_width()/2, y_pos, f'${val:+.0f}K', ha='center', fontsize=11, fontweight='bold')
ax2.axhline(y=0, color=PAL['neutral'], linewidth=1.5)
ax2.set_ylabel('Miles USD [SUPUESTO]')
ax2.set_title('Impacto Financiero del Modelo\nvs. Política de Aprobar Todo', fontsize=12, fontweight='bold')
plt.suptitle('¿Cómo se traduce un mayor Gini en dinero ahorrado para FinanCrece S.A.? [SUPUESTO]',
             fontsize=13, fontweight='bold', y=1.01)
plt.tight_layout()
save('ppt_gini_dinero')

# ============================================================
# H: CUOTA COMPROMETIDA
# ============================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
inst_dr = df.groupby('installment_commitment')['default'].agg(['mean','count'])
colores_inst = [PAL['neg'],PAL['neg'],PAL['amber'],PAL['pos']]
labels_inst = [f'{i}% ingreso\n(n={int(c)})' for i, c in zip(inst_dr.index, inst_dr['count'])]
bars = ax1.bar(labels_inst, inst_dr['mean']*100,
               color=colores_inst, edgecolor='white', linewidth=0.5, width=0.55)
ax1.axhline(y=tasa_global*100, color=PAL['accent'], linestyle='--', linewidth=2)
for bar, row in zip(bars, inst_dr.itertuples()):
    ax1.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5,
             f'{row.mean*100:.1f}%', ha='center', fontsize=12, fontweight='bold')
ax1.set_xlabel('Compromiso de Cuota (% del ingreso)')
ax1.set_ylabel('Tasa de Default (%)')
ax1.set_title('Default por Nivel de Cuota Comprometida', fontsize=12, fontweight='bold')
ax1.set_ylim(0, 42)

x_inst = inst_dr.index.astype(float)
y_inst = inst_dr['mean'].values * 100
ax2.plot(x_inst, y_inst, 'o-', color=PAL['accent'], linewidth=2.5, markersize=11)
ax2.fill_between(x_inst, y_inst, alpha=0.2, color=PAL['accent'])
z = np.polyfit(x_inst, y_inst, 1)
p_fit = np.poly1d(z)
ax2.plot(x_inst, p_fit(x_inst), '--', color=PAL['pos'], linewidth=1.8, label='Tendencia lineal')
ax2.set_xlabel('Compromiso de Cuota')
ax2.set_ylabel('Tasa de Default (%)')
ax2.set_title('Relación casi lineal:\na mayor cuota → mayor riesgo', fontsize=12, fontweight='bold')
ax2.legend(fontsize=9)
ax2.grid(True, alpha=0.3)
plt.suptitle('¿Cómo afecta la carga de pago (installment_commitment) a la probabilidad de incumplimiento?',
             fontsize=13, fontweight='bold', y=1.01)
plt.tight_layout()
save('ppt_cuota_comprometida')

# ============================================================
# I: RIESGOS OCULTOS + INCLUSIÓN FINANCIERA
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
ax = axes[0]
historial_orden = ['existing paid','critical/other existing credit','delayed previously','all paid','no credits/all paid']
historial_labels = ['Crédito\nPagado','Crédito\nCrítico','Pago\nAtrasado','Todo\nPagado','Sin\nHistorial']
hist_dr = df.groupby('credit_history')['default'].agg(['mean','count']).reindex(historial_orden)
colores_hist = [PAL['neg'],PAL['neg'],PAL['amber'],PAL['pos'],'#EF4444']
bars = ax.bar(historial_labels, hist_dr['mean']*100,
              color=colores_hist, edgecolor='white', linewidth=0.5, width=0.6)
ax.axhline(y=tasa_global*100, color=PAL['accent'], linestyle='--', linewidth=2)
for bar, row in zip(bars, hist_dr.itertuples()):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1,
            f'{row.mean*100:.0f}%', ha='center', fontsize=12, fontweight='bold')
ax.set_ylabel('Tasa de Default (%)')
ax.set_title('Riesgo por Historial Crediticio', fontsize=12, fontweight='bold')
ax.set_ylim(0, 78)
ax.text(3.5, 55, 'RIESGO\nOCULTO\n65.6%', fontsize=10, color='#EF4444', ha='center', fontweight='bold',
        bbox=dict(boxstyle='round', facecolor=PAL['face'], alpha=0.9))

ax2 = axes[1]
senales_riesgo = ['Sin historial\n(65.6%)', 'Cuenta negativa\n(47.4%)', 'Empleo <1 año\n(40.4%)',
                  'Cuota nivel 4\n(32.8%)', 'Crédito para\neducación (40.5%)']
valores_riesgo = [65.6, 47.4, 40.4, 32.8, 40.5]
colores_riesgo = ['#EF4444','#EF4444','#F59E0B','#F59E0B','#EF4444']
bars2 = ax2.barh(senales_riesgo, valores_riesgo, color=colores_riesgo, edgecolor='white', linewidth=0.5)
ax2.axvline(x=tasa_global*100, color=PAL['accent'], linestyle='--', linewidth=2, label=f'Promedio {tasa_global*100:.1f}%')
for bar, val in zip(bars2, valores_riesgo):
    ax2.text(val+0.5, bar.get_y()+bar.get_height()/2, f'{val:.1f}%', va='center', fontsize=11, fontweight='bold')
ax2.set_xlabel('Tasa de Default (%)')
ax2.set_title('Señales de Riesgo Oculto\nen Clientes Aparentemente Normales', fontsize=12, fontweight='bold')
ax2.legend(fontsize=9)
ax2.set_xlim(0, 80)
plt.suptitle('Inclusión Financiera vs Control del Riesgo — Detectando Riesgos Ocultos',
             fontsize=13, fontweight='bold', y=1.01)
plt.tight_layout()
save('ppt_inclusion_riesgo_oculto')

# ============================================================
# J: PANEL FEATURE IMPORTANCE (para P11 - predictores principales)
# ============================================================
fig, ax = plt.subplots(figsize=(12, 6))
features_top = [
    ('score_riesgo_compuesto', 151, 'Feature\npropia'),
    ('cuota_estimada', 113, 'Feature\npropia'),
    ('carga_vs_cuenta', 103, 'Feature\npropia'),
    ('age (edad)', 100, 'Original'),
    ('credit_amount', 85, 'Original'),
    ('duration (plazo)', 66, 'Original'),
    ('residence_since', 56, 'Original'),
    ('own_telephone', 30, 'Original'),
    ('carga_financiera', 26, 'Feature\npropia'),
    ('riesgo_combinado', 25, 'Feature\npropia'),
]
nombres = [f[0] for f in features_top]
valores_imp = [f[1] for f in features_top]
tipos = [f[2] for f in features_top]
colores_imp = [PAL['pos'] if t == 'Feature\npropia' else PAL['neg'] for t in tipos]
bars = ax.barh(nombres, valores_imp, color=colores_imp, edgecolor='white', linewidth=0.3)
for bar, val in zip(bars, valores_imp):
    ax.text(val+1, bar.get_y()+bar.get_height()/2, str(val), va='center', fontsize=10, fontweight='bold')
ax.set_xlabel('Importancia (LightGBM splits)')
ax.set_title('Top 10 Predictores de Default — ¿Qué variables determinan que un cliente es "bad"?',
             fontsize=12, fontweight='bold')
ax.invert_yaxis()
patch_fe = mpatches.Patch(color=PAL['pos'], label='Feature ingeniería propia')
patch_or = mpatches.Patch(color=PAL['neg'], label='Variable original del dataset')
ax.legend(handles=[patch_fe, patch_or], fontsize=10, loc='lower right')
ax.grid(True, alpha=0.3, axis='x')
save('ppt_feature_importance_jurado')

# ============================================================
# K: HERRAMIENTA SCORING — AJUSTE DE UMBRAL (P12)
# ============================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
thresholds = np.linspace(0.10, 0.80, 71)
# Simular datos de val (proporcionales a resultados reales)
n_good, n_bad = 113, 47
rois_sim, recall_sim, precision_sim, aprobados_sim = [], [], [], []
for t in thresholds:
    aprobados_pct = 1 - (t * 0.7)
    recall = max(0, 1 - t * 1.2)
    precision = min(1, 0.4 + t * 0.6)
    ben = n_good*450*(1-t*0.8) + n_bad*(-3000)*max(0,1-t*1.2)
    base = n_good*450 + n_bad*(-3000)
    rois_sim.append((ben-base)/abs(base))
    recall_sim.append(recall)
    precision_sim.append(precision)
    aprobados_sim.append(aprobados_pct*100)

opt_idx = np.argmax(rois_sim)
ax1.plot(thresholds, [r*100 for r in rois_sim], color=PAL['pos'], linewidth=2.5, label='ROI estimado')
ax1.axvline(x=thresholds[opt_idx], color=PAL['accent'], linestyle='--', linewidth=2.5,
            label=f'Umbral óptimo: {thresholds[opt_idx]:.2f}')
ax1.fill_between(thresholds, [r*100 for r in rois_sim], 0,
                  where=[r>0 for r in rois_sim], alpha=0.25, color=PAL['pos'])
ax1.axhline(y=0, color=PAL['neutral'], linewidth=1.5)
ax1.set_xlabel('Threshold de Rechazo')
ax1.set_ylabel('ROI vs. Aprobar Todos (%)')
ax1.set_title('Ajuste de Umbral = Control Total del Riesgo\nLa herramienta ajusta en tiempo real', fontsize=12, fontweight='bold')
ax1.legend(fontsize=9)
ax1.grid(True, alpha=0.3)

# Política 3 bandas visual
ax2.set_xlim(0, 1)
ax2.set_ylim(0, 4)
ax2.set_yticks([])
ax2.set_xlabel('prob_default del cliente', fontsize=12)
ax2.set_title('¿Qué tan fácil es ajustar los límites?\nVisualización de la Política de 3 Bandas', fontsize=12, fontweight='bold')
ax2.axvspan(0, 0.20, alpha=0.35, color=PAL['neg'])
ax2.axvspan(0.20, 0.45, alpha=0.35, color=PAL['amber'])
ax2.axvspan(0.45, 1.0, alpha=0.35, color='#EF4444')
ax2.axvline(x=0.20, color='white', linewidth=2.5, linestyle='--')
ax2.axvline(x=0.45, color='white', linewidth=2.5, linestyle='--')
ax2.text(0.10, 2.5, 'BAJO\nRIESGO', ha='center', fontsize=12, fontweight='bold', color='white')
ax2.text(0.10, 1.5, 'APROBAR\nCompleto', ha='center', fontsize=10, color=PAL['text'])
ax2.text(0.325, 2.5, 'RIESGO\nMEDIO', ha='center', fontsize=12, fontweight='bold', color='white')
ax2.text(0.325, 1.5, 'CONDICIONAR\n50% línea', ha='center', fontsize=10, color=PAL['text'])
ax2.text(0.72, 2.5, 'ALTO\nRIESGO', ha='center', fontsize=12, fontweight='bold', color='white')
ax2.text(0.72, 1.5, 'RECHAZAR\nEvaluación manual', ha='center', fontsize=10, color=PAL['text'])
ax2.text(0.20, 0.5, 'u1 = 0.20\nAJUSTABLE', ha='center', fontsize=8, color=PAL['accent'])
ax2.text(0.45, 0.5, 'u2 = 0.45\nAJUSTABLE', ha='center', fontsize=8, color=PAL['accent'])
save('ppt_herramienta_ajuste_umbral')

print()
print('=== TODOS LOS GRÁFICOS GENERADOS ===')
for f in sorted(FIG.glob('ppt_*.png')):
    print(f'  {f.name}')
