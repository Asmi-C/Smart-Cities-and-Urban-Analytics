"""Out-of-date calibration reliability; bin counts never treated as independent dates."""
from pathlib import Path
import pandas as pd,numpy as np
R=Path(__file__).resolve().parents[1];T=R/'outputs/tables'
df=pd.read_csv(T/'hotspot_probability_predictions.csv')
df['bin']=pd.cut(df.hotspot_probability,bins=np.linspace(0,1,11),include_lowest=True)
out=df.groupby(['model','date','bin'],observed=True).agg(n=('hex_id','size'),
    mean_predicted_probability=('hotspot_probability','mean'),
    observed_hotspot_fraction=('hotspot_truth_eval_only','mean')).reset_index()
out.to_csv(T/'hotspot_reliability_bins.csv',index=False)
ece=[]
for (model,date),z in out.groupby(['model','date']):
    score=(z.n*(z.mean_predicted_probability-z.observed_hotspot_fraction).abs()).sum()/z.n.sum()
    ece.append({'model':model,'date':date,'ECE_10bin':score})
pd.DataFrame(ece).to_csv(T/'hotspot_calibration_ECE.csv',index=False)
