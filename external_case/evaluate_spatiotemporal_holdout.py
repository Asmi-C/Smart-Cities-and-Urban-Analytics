"""Six-date leave-one-date-out AND geographic 1km group holdout.

For each test date and geographic fold, remove the same geographic blocks
from ALL source-date training data. Target labels enter metrics only.
"""
from pathlib import Path
import numpy as np,pandas as pd,geopandas as gpd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold
from sklearn.metrics import mean_squared_error,r2_score,mean_absolute_error
from scipy.stats import spearmanr
R=Path(__file__).resolve().parents[1];F=['NDVI','NDBI','MNDWI']
ids=pd.read_csv(R/'data/selected_acquisitions.csv').item_id.tolist()
g=gpd.read_file(R/'outputs/data/hex_results.gpkg').to_crs(32645).set_index('hex_id')
xy=np.c_[g.geometry.centroid.x,g.geometry.centroid.y]
bins=np.floor((xy-xy.min(0))/1000).astype(int)
blocks=pd.Series(bins[:,0]*10000+bins[:,1],index=g.index)
S={}
for item in ids:
    date=item.split('_')[3];t=pd.read_csv(R/f'external_case/data/landsat_hex_{item[:4]}_{date}.csv')
    t=t.loc[np.isfinite(t[['LST']+F]).all(axis=1)].reset_index(drop=True)
    t['block']=t.hex_id.map(blocks);S[date]=t
rows=[];pred_rows=[]
for held,test in S.items():
    sources=[s for date,s in S.items() if date!=held]
    groups=test.block.to_numpy();splits=GroupKFold(5).split(test,groups=groups)
    pred_abs=np.full(len(test),np.nan);pred_an=np.full(len(test),np.nan)
    for fold,(train_target_indices,te) in enumerate(splits):
        held_blocks=set(groups[te]);src=[s.loc[~s.block.isin(held_blocks)] for s in sources]
        X=np.vstack([s[F].to_numpy() for s in src])
        abs_y=np.concatenate([s.LST.to_numpy() for s in src])
        an_y=np.concatenate([s.LST.to_numpy()-s.LST.mean() for s in src])
        assert not any(s.block.isin(held_blocks).any() for s in src)
        for y,arr in [(abs_y,pred_abs),(an_y,pred_an)]:
            model=RandomForestRegressor(n_estimators=120,min_samples_leaf=5,max_features=.8,random_state=42,n_jobs=-1)
            arr[te]=model.fit(X,y).predict(test.iloc[te][F])
    for name,truth,pred in [('absolute_C',test.LST.to_numpy(),pred_abs),
                            ('mean_anomaly_C',test.LST.to_numpy()-test.LST.mean(),pred_an)]:
        assert np.isfinite(pred).all()
        rows.append({'heldout_date':held,'target':name,'n_test_hex':len(test),
            'n_outer_geographic_folds':5,'RMSE':np.sqrt(mean_squared_error(truth,pred)),
            'MAE':mean_absolute_error(truth,pred),'R2':r2_score(truth,pred),
            'Spearman':spearmanr(truth,pred).statistic,'no_same_date_training':True,
            'no_same_geographic_block_training':True,
            'target_mean_only_for_anomaly_evaluation':name=='mean_anomaly_C'})
        for hid,p,t in zip(test.hex_id,pred,truth):pred_rows.append({'test_date':held,'hex_id':hid,'target':name,'predicted':p,'actual':t})
out=pd.DataFrame(rows);out.to_csv(R/'outputs/tables/spatiotemporal_holdout.csv',index=False)
pd.DataFrame(pred_rows).to_csv(R/'outputs/tables/spatiotemporal_holdout_predictions.csv',index=False)
print(out[['heldout_date','target','n_test_hex','RMSE','R2','Spearman']].to_string(index=False))
