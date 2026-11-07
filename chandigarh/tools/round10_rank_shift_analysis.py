"""Postprocess fixed D0–D3 matrix; rank reversals, optimism, domain-level inference."""
from itertools import product,combinations
from pathlib import Path
import numpy as np,pandas as pd
from scipy.stats import kendalltau,spearmanr
R=Path(__file__).resolve().parents[1];P=R/'outputs/tables'
d=pd.read_csv(P/'domain_shift_model_matrix_long.csv')
w=d.groupby(['model','regime']).R2.mean().unstack()
rank=w.rank(axis=0,ascending=False,method='min').astype(int)
rows=[]
for a,b in combinations(['D0','D1','D2','D3'],2):
    k,kp=kendalltau(w[a],w[b]);s,sp=spearmanr(w[a],w[b]);rows.append({'regime_A':a,'regime_B':b,'Kendall_tau':k,'Spearman_rho':s,'best_A':w[a].idxmax(),'best_B':w[b].idxmax(),'top_model_reversal':w[a].idxmax()!=w[b].idxmax()})
pd.DataFrame(rows).to_csv(P/'model_rank_reversal.csv',index=False)
rank.to_csv(P/'model_rank_by_regime.csv')
opt=[];rng=np.random.default_rng(551)
for name,g in d[d.regime=='D3'].groupby('model'):
    for easy in ['D0','D1','D2']:
        e=d[(d.regime==easy)&(d.model==name)]
        gap=e.R2.mean()-g.R2.mean()
        years=np.array(sorted(set(e.year)|set(g.year)))
        by_year_easy=e.groupby('year').R2.mean();by_year_hard=g.groupby('year').R2.mean()
        common=sorted(set(by_year_easy.index)&set(by_year_hard.index));y=(by_year_easy.loc[common]-by_year_hard.loc[common]).to_numpy()
        bs=rng.choice(y,size=(20000,len(y)),replace=True).mean(1)
        signs=np.array(list(product([-1,1],repeat=len(y))))
        p=np.mean(np.abs((signs*y).mean(1))>=abs(y.mean())-1e-14)
        opt.append({'model':name,'easy_regime':easy,'hard_regime':'D3','mean_R2_optimism':gap,'equal_years_mean_optimism':y.mean(),'year_cluster_CI_low':np.quantile(bs,.025),'year_cluster_CI_high':np.quantile(bs,.975),'year_cluster_signflip_p':p,'n_years':len(y)})
pd.DataFrame(opt).to_csv(P/'validation_optimism.csv',index=False)
print('Rank ordering, highest R2 first:\n',rank.sort_values('D3'))
print('Optimism:\n',pd.DataFrame(opt).round(3).to_string(index=False))

