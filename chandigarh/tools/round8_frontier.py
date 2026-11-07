"""Honest multiobjective table; incomparable targets are explicitly separated."""
from pathlib import Path
import pandas as pd
R=Path(__file__).resolve().parents[1];T=R/'outputs/tables'
rows=[]
d=pd.read_csv(T/'date_level_method_comparison_long.csv')
for model,g in d.groupby('model'):
    rows.append({'task':'relative_anomaly_regression','model':model,'dates':g.date.nunique(),
        'mean_anomaly_R2':g.R2.mean(),'mean_anomaly_RMSE_C':g.RMSE.mean(),
        'mean_residual_Moran_I':g.Moran_I.mean(),
        'mean_fit_seconds':g.runtime_seconds_including_source_OOD_correction.mean() if 'runtime_seconds_including_source_OOD_correction' in g else None})
h=pd.read_csv(T/'persistent_hotspot_prediction.csv')
for model,g in h.groupby('model'):
    rows.append({'task':'top_quintile_hotspot_classification','model':model,'dates':g.date.nunique(),
        'mean_AUROC':g.AUROC.mean(),'mean_PR_AUC':g.PR_AUC.mean(),'mean_Brier':g.Brier.mean()})
m=pd.read_csv(T/'meteorology_ablation.csv')
for model,g in m.groupby('model'):
    rows.append({'task':'absolute_temperature_regression','model':model,'dates':g.date.nunique(),
        'mean_absolute_RMSE_C':g.RMSE_C.mean(),'mean_absolute_R2':g.R2.mean(),
        'mean_date_bias_C':g.date_mean_error_C.mean()})
c=pd.read_csv(T/'date_conformal_coverage.csv')
for (method,nominal),g in c.groupby(['calibration','nominal']):
    rows.append({'task':'anomaly_prediction_interval','model':method,'dates':g.date.nunique(),
        'nominal_coverage':nominal,'mean_empirical_coverage':g.empirical_coverage.mean(),
        'worst_date_coverage':g.empirical_coverage.min(),'mean_interval_width_C':g.mean_interval_width_C.mean()})
pd.DataFrame(rows).to_csv(T/'model_selection_frontier.csv',index=False)
