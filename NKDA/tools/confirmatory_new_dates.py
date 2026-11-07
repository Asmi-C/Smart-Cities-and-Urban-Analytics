"""Predeclared addition-only tests; exclude six previously inspected acquisitions."""
from pathlib import Path
from itertools import product
import numpy as np,pandas as pd
R=Path(__file__).resolve().parents[1];F=R/'outputs/tables'
old=set(pd.read_csv(R/'data/selected_acquisitions.csv').item_id.str.split('_').str[3])
d=pd.read_csv(F/'date_level_method_comparison.csv');d.Date=d.Date.astype(str)
added=d[~d.Date.isin(old)].copy();newhot=pd.read_csv(F/'persistent_hotspot_prediction.csv')
newhot.date=newhot.date.astype(str);newhot=newhot[~newhot.date.isin(old)]
if len(added)<4:
    print('Additional-domain confirmation blocked: only',len(added),'added dates');raise SystemExit(0)
def stats(name,delta,wins_when_positive=True):
    delta=np.array(delta,dtype=float);n=len(delta);rng=np.random.default_rng(101)
    b=np.mean(rng.choice(delta,size=(20000,n),replace=True),axis=1)
    year=pd.DataFrame({'year':added.Date.str[:4].to_numpy(),'delta':delta}).groupby('year').delta.mean().to_numpy()
    by=np.mean(rng.choice(year,size=(20000,len(year)),replace=True),axis=1)
    signs=np.array(list(product([-1,1],repeat=len(year))))
    return {'comparison':name,'new_dates':n,'years':len(year),'mean_delta':float(delta.mean()),
       'wins':int((delta>0).sum() if wins_when_positive else (delta<0).sum()),
       'new_date_boot_CI_low':float(np.quantile(b,.025)),'new_date_boot_CI_high':float(np.quantile(b,.975)),
       'year_boot_CI_low':float(np.quantile(by,.025)),'year_boot_CI_high':float(np.quantile(by,.975)),
       'year_signflip_p':float(np.mean(np.abs((signs*year).mean(axis=1))>=abs(year.mean())-1e-14))}
rows=[stats('hybrid_minus_zRF_anomaly_R2',added.delta_R2),
      stats('hybrid_minus_site_climatology_anomaly_R2',added.delta_proposed_vs_climatology_R2)]
h=newhot.pivot(index='date',columns='model',values=['AUROC','Brier'])
for metric in ['AUROC','Brier']:
    vals=(h[(metric,'source_hotspot_frequency')]-h[(metric,'RF_hotspot_classifier')]).reindex(added.Date).to_numpy()
    rows.append(stats('site_frequency_minus_RF_hotspot_'+metric,vals,wins_when_positive=metric!='Brier'))
out=pd.DataFrame(rows);out.to_csv(F/'addition_only_confirmatory_tests.csv',index=False)
print(out.round(4).to_string(index=False))
