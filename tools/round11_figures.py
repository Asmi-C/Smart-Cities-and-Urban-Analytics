"""Figures for Round 11: optimism across holdout geometries; D3 interval coverage."""
from pathlib import Path
import pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]; T=R/'outputs/tables'; F=R/'paper/figures'
S=pd.read_csv(T/'round11_optimism_summary.csv')
names={'ridge_z':'Ridge','RF_z':'RF','HGB_z':'HGB','RF_z_coords':'RF + coords'}
cols={'ridge_z':'#4C72B0','RF_z':'#55A868','HGB_z':'#C44E52','RF_z_coords':'#8172B2'}
cfgs=sorted(S.config.unique(),key=lambda c:(c[0],c))
fig,axes=plt.subplots(1,2,figsize=(10,4.2),sharey=True)
for ax,sen in zip(axes,['Landsat8','Landsat9']):
    for j,m in enumerate(names):
        g=S[(S.sensor==sen)&(S.model==m)].set_index('config').loc[cfgs]
        y=np.arange(len(cfgs))+(j-1.5)*0.18
        ax.errorbar(g.mean_gap,y,xerr=[g.mean_gap-g.CI95_low_twoway,g.CI95_high_twoway-g.mean_gap],fmt='o',ms=4,color=cols[m],label=names[m],capsize=2,lw=1)
    ax.axvline(0,color='k',lw=.8);ax.set_xlabel('Paired optimism  R²(D2) − R²(D3)')
    ax.set_title(f"{sen}: {'15 development dates' if sen=='Landsat8' else '5 frozen confirmation dates'}",fontsize=10)
    ax.grid(axis='x',alpha=.3)
axes[0].set_yticks(range(len(cfgs)));axes[0].set_yticklabels([c.replace('_o0',' origin A').replace('_o5',' origin B').replace('_b0','').replace('_b500',' +500 m buffer') for c in cfgs],fontsize=8)
h,l=axes[1].get_legend_handles_labels();fig.legend(h,l,loc='lower center',ncol=4,fontsize=8,frameon=False);fig.tight_layout(rect=(0,0.06,1,1));fig.savefig(F/'fig_optimism_geometries.png',dpi=200)
C=pd.read_csv(T/'round11_interval_coverage.csv')
fig,ax=plt.subplots(figsize=(6,4))
for (test,rule),g in C.groupby(['test','rule']):
    a=g.groupby('nominal').coverage.agg(['mean','min'])
    ls='-' if rule=='date_cluster' else '--'; c='#C44E52' if test.startswith('L8') else '#4C72B0'
    ax.plot(a.index,a['mean'],ls,color=c,marker='o',label=f"{'L8 leave-year-out' if test.startswith('L8') else 'L8→L9'} · {rule.replace('_',' ')} (mean)")
    ax.plot(a.index,a['min'],ls,color=c,marker='x',alpha=.5,label=f"… worst date")
ax.plot([.78,.97],[.78,.97],'k:',lw=1);ax.set_xlabel('Nominal coverage');ax.set_ylabel('Empirical D3 coverage');ax.legend(fontsize=6.5);ax.grid(alpha=.3)
fig.tight_layout();fig.savefig(F/'fig_d3_interval_coverage.png',dpi=200);print('ok')
