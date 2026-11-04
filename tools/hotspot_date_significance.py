"""Date/cluster-level inference for strongest simple site-frequency hotspot baseline."""
from pathlib import Path
from itertools import product
import numpy as np,pandas as pd
R=Path(__file__).resolve().parents[1];T=R/'outputs/tables'
data=pd.read_csv(T/'persistent_hotspot_prediction.csv')
out=data.pivot(index='date',columns='model',values=['AUROC','Brier','PR_AUC'])
rows=[];rng=np.random.default_rng(84)
for metric in ['AUROC','Brier','PR_AUC']:
    delta=(out[(metric,'source_hotspot_frequency')]-out[(metric,'RF_hotspot_classifier')]).to_numpy()
    n=len(delta)
    signs=np.array(list(product([-1,1],repeat=n))) if n<=18 else None
    pv=float(np.mean(np.abs((signs*delta).mean(axis=1))>=abs(delta.mean())-1e-14)) if signs is not None else np.nan
    boot=np.mean(rng.choice(delta,size=(10000,n),replace=True),axis=1)
    years=pd.Series(out.index.astype(str)).str[:4].to_numpy()
    byyear=pd.DataFrame({'year':years,'delta':delta}).groupby('year').delta.mean().to_numpy()
    yboot=np.mean(rng.choice(byyear,size=(10000,len(byyear)),replace=True),axis=1)
    rows.append({'metric':'source_frequency_minus_RF_'+metric,'n_dates':n,'n_calendar_years':len(byyear),
      'mean_delta':delta.mean(),'wins':int((delta>0).sum()) if metric!='Brier' else int((delta<0).sum()),
      'date_boot_CI_low':np.quantile(boot,.025),'date_boot_CI_high':np.quantile(boot,.975),
      'year_cluster_CI_low':np.quantile(yboot,.025),'year_cluster_CI_high':np.quantile(yboot,.975),
      'date_signflip_p_exploratory':pv})
pd.DataFrame(rows).to_csv(T/'hotspot_date_significance.csv',index=False)
print(pd.DataFrame(rows).round(4).to_string(index=False))
