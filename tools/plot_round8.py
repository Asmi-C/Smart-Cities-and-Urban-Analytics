"""Scientific plots with explicit date-level units; no decorative graphics."""
from pathlib import Path
import pandas as pd,numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];T=R/'outputs/tables';O=R/'outputs/figures';O.mkdir(exist_ok=True,parents=True)
raw=pd.read_csv(T/'date_level_method_comparison_long.csv');p=raw.pivot(index='date',columns='model',values='R2').sort_index()
fig,ax=plt.subplots(figsize=(11,5));models=['RF_raw','RF_zsource_ztarget','RF_z_plus_source_spatial_bias','source_spatial_climatology']
colors=['#666666','#377eb8','#e41a1c','#4daf4a']
for name,color in zip(models,colors):
    ax.plot(np.arange(len(p)),p[name],marker='o',lw=1.5,label=name.replace('_',' '),color=color)
ax.axhline(0,color='black',lw=.7);ax.set_xticks(range(len(p)),p.index.astype(str),rotation=50,ha='right')
ax.set_ylabel('Held-date R², acquisition mean-centered LST anomaly');ax.set_xlabel('Fully held-out acquisition')
ax.legend(fontsize=8,ncol=2);fig.tight_layout();fig.savefig(O/'round8_anomaly_model_comparison.png',dpi=190);plt.close(fig)
hot=pd.read_csv(T/'persistent_hotspot_prediction.csv');h=hot.pivot(index='date',columns='model',values='AUROC').sort_index()
fig,ax=plt.subplots(figsize=(11,4));x=np.arange(len(h));w=.38
ax.bar(x-w/2,h['RF_hotspot_classifier'],w,label='Spectral RF classifier',color='#377eb8')
ax.bar(x+w/2,h['source_hotspot_frequency'],w,label='Historical site-hotspot frequency',color='#4daf4a')
ax.set_xticks(x,h.index.astype(str),rotation=50,ha='right');ax.set_ylim(0,1);ax.set_ylabel('Held-acquisition hotspot AUROC')
ax.legend(fontsize=9);fig.tight_layout();fig.savefig(O/'round8_hotspot_probability_comparison.png',dpi=190);plt.close(fig)
weather=pd.read_csv(T/'meteorology_ablation.csv');v=weather.pivot(index='date',columns='model',values='RMSE_C').sort_index()
fig,ax=plt.subplots(figsize=(11,4));x=np.arange(len(v))
for name in ['source_mean_plus_spatial_climatology','meteorology_plus_spatial_climatology','meteorology_plus_hybrid']:
    if name in v:ax.plot(x,v[name],marker='o',label=name.replace('_',' '))
ax.set_xticks(x,v.index.astype(str),rotation=50,ha='right');ax.set_ylabel('Held-acquisition absolute LST RMSE (°C)')
ax.legend(fontsize=8);fig.tight_layout();fig.savefig(O/'round8_meteorology_absolute_transfer.png',dpi=190);plt.close(fig)
print('Wrote three Round-8 diagnostic figures')
