"""Exploratory 4-quadrant x 15-date held-location+date evaluation.

No historical outcomes from held-out geography enter feature or residual training.
Fixed 8-neighbour IDW gives simple site-climatology a fair unseen-site fallback.
"""
from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error, roc_auc_score

R=Path(__file__).resolve().parents[1]
F=['NDVI','NDBI','MNDWI']
scenes=pd.read_csv(R/'data/selected_acquisitions_final.csv').item_id
A={}
for item in scenes:
    day=item.split('_')[3]
    d=pd.read_csv(R/f'external_case/data/landsat_hex_LC08_{day}.csv')
    d=d[np.isfinite(d[['LST']+F]).all(axis=1)].copy()
    if len(d)>=180:A[day]=d
con=sqlite3.connect(R/'outputs/data/hex_results.gpkg')
coords=pd.read_sql_query('SELECT h.hex_id,(r.minx+r.maxx)/2 x,(r.miny+r.maxy)/2 y FROM hex_results h JOIN rtree_hex_results_geom r ON h.fid=r.id',con).set_index('hex_id')
con.close()
cutx,cuty=coords.x.median(),coords.y.median()
quadrant=((coords.x>cutx).astype(int)*2+(coords.y>cuty).astype(int)).rename('quadrant')
for day in A:
    A[day]=A[day].join(quadrant,on='hex_id').join(coords,on='hex_id')

def model():
    return RandomForestRegressor(n_estimators=45,min_samples_leaf=5,max_features=.8,random_state=42,n_jobs=-1)

def standard(a):return (a-a.mean(0))/(a.std(0)+1e-6)

def idw(train_xy,train_values,test_xy,k=8):
    if len(train_xy)==0:return np.zeros(len(test_xy))
    d,ix=cKDTree(train_xy).query(test_xy,k=min(k,len(train_xy)))
    if d.ndim==1:d=d[:,None];ix=ix[:,None]
    w=1/(d+1)**2
    return (w*train_values[ix]).sum(1)/w.sum(1)

def source_data(days,block):
    ds=[];labels=[]
    for day in days:
        d=A[day][A[day].quadrant!=block].copy()
        d['anomaly']=d.LST-d.LST.mean()
        ds.append(d)
        labels.extend(d.anomaly)
    return ds,np.asarray(labels)

rows=[]
for block in range(4):
    for held_day in sorted(A):
        source_days=sorted(set(A)-{held_day})
        train,ys=source_data(source_days,block)
        test=A[held_day][A[held_day].quadrant==block].copy()
        if len(test)<15:continue
        history=pd.concat(train).groupby('hex_id',sort=False).agg(x=('x','first'),y=('y','first'),anomaly=('anomaly','mean'))
        historical=idw(history[['x','y']].to_numpy(),history.anomaly.to_numpy(),test[['x','y']].to_numpy())
        xx=np.vstack([standard(d[F].to_numpy()) for d in train]);tt=standard(test[F].to_numpy())
        spectral=model().fit(xx,ys).predict(tt)
        # Source-only out-of-acquisition residuals, trained on training geography exclusively.
        errs=[]
        for i,d in enumerate(train):
            x_inner=np.vstack([standard(other[F].to_numpy()) for j,other in enumerate(train) if j!=i])
            y_inner=np.concatenate([other.anomaly.to_numpy() for j,other in enumerate(train) if j!=i])
            pred=model().fit(x_inner,y_inner).predict(standard(d[F].to_numpy()))
            rr=d[['hex_id','x','y']].copy();rr['residual']=d.anomaly.to_numpy()-pred
            errs.append(rr)
        spatial=pd.concat(errs).groupby('hex_id',sort=False).agg(x=('x','first'),y=('y','first'),residual=('residual','mean'))
        spatial_bias=idw(spatial[['x','y']].to_numpy(),spatial.residual.to_numpy(),test[['x','y']].to_numpy())
        hybrid=spectral+.5*spatial_bias
        truth=test.LST.to_numpy()-A[held_day].LST.mean() # evaluation only, never used in fit
        hot=(test.LST.to_numpy()>=A[held_day].LST.quantile(.8)).astype(int)
        for name,pred in [('normalized_RF',spectral),('historical_climatology_IDW',historical),('RF_plus_spatial_residual_IDW',hybrid)]:
            auroc=roc_auc_score(hot,pred) if np.unique(hot).size==2 else np.nan
            rows.append({'held_date':held_day,'year':held_day[:4],'held_quadrant':block,'model':name,'n_hex':len(test),'R2':r2_score(truth,pred),'RMSE':np.sqrt(mean_squared_error(truth,pred)),'hotspot_AUROC':auroc})
        print('Held block/date',block,held_day,len(test),flush=True)

out=pd.DataFrame(rows)
out.to_csv(R/'outputs/tables/unseen_site_unseen_date.csv',index=False)
print(out.groupby('model')[['R2','RMSE','hotspot_AUROC']].mean().round(4))
