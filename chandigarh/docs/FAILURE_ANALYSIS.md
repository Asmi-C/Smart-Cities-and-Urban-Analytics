# Out-of-fold model failures

Baseline RF exhibits spatially clustered positive and negative residuals (8NN Moran I 0.439, p=0.001), and uneven geographic fold error. Detailed per-fold errors and the original signed-residual map are available in `outputs/tables/residual_fold_summary.csv` and `outputs/PPT_FIGURES/08_residual_diagnostics.png`.

Absolute coordinates reduce geographically held-out RMSE, with better 1-km block outcomes across the 12 tested block origins and 2 seeds. Mean residual Moran I remains positive, so persistent unmodelled neighborhood effects, sensor/view/weather influences or missing built-form variables remain plausible. The present data do not permit attributing these errors causally to roads, building heights or land-use classes. These are hypotheses for independent layer/field validation.

No individual hex was designated a real-world 'failure cause' without verified field context. The neighborhood context ablation worsens RMSE, while target-safe residual-neighbor correction lowers Moran I but worsens RMSE; these are genuine methodological failures retained in the paper.
