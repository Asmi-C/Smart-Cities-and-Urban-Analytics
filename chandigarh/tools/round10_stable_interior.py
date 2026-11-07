"""Scenario-stable interior robustness for joint D3 predictions only.

Interior based on original digitized polygon under 640m and 962m rigid shifts;
not a cadastral or probability-based boundary confidence region.
"""
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.metrics import r2_score,mean_squared_error
R=Path(__file__).resolve().parents[1];P=R/'outputs/tables'
core=set(pd.read_csv(P/'boundary_stable_interior_640m.csv').hex_id)
d=pd.read_csv(P/'round10_joint_domain_predictions.csv');d['stable_interior']=d.hex_id.isin(core)
rows=[]
for (date,block,model),g in d.groupby(['held_date','held_quadrant','model']):
    for part in ['all','scenario_640m_stable_core']:
        s=g if part=='all' else g[g.stable_interior]
        if len(s)<15:continue
        rows.append({'date':date,'year':str(date)[:4],'quadrant':block,'model':model,'support':part,'n':len(s),'R2':r2_score(s.true_anomaly,s.prediction),'RMSE':np.sqrt(mean_squared_error(s.true_anomaly,s.prediction))})
out=pd.DataFrame(rows);out.to_csv(P/'stable_interior_joint_shift.csv',index=False)
print(out.groupby(['support','model'])[['R2','RMSE','n']].agg({'R2':'mean','RMSE':'mean','n':'sum'}).round(3))
print('D3 core eligible geo/date folds',out.query('support=="scenario_640m_stable_core"').groupby('model').size().to_dict())
