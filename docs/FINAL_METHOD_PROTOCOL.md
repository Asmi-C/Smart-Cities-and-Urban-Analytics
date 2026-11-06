# Round 8 frozen experiment protocol (defined before expanded-date outcomes)

Primary question: Can a source-date-trained model predict relative heat on an entirely unseen Landsat acquisition, with no held-out acquisition LST used in fit, adaptation, tuning or prediction?

## Acquisition cohort

- Landsat-8 Collection-2 Level-2, WRS 138/045, L2SP, Tier 1; 2018-2026; 15 February–15 May; scene cloud fraction ≤25%.
- For each year select at most two lowest-cloud scenes separated by ≥16 days. Pre-existing six dates remain regardless of candidate ranking, as the original frozen cohort; all qualifying selected additions form an **expanded, exploratory** cohort.
- Require ≥180 complete NKDA hexes on ST/reflectance features. Exclude low-overlap dates only by this predeclared availability rule, before looking at scores. Preserve all catalog and quality-screening exclusions.
- Avoid treating 2 dates in one year as independent climate years; report date-level tests with the year-cluster caveat.

## Primary and secondary endpoints

- **Primary:** paired change in leave-one-date-out mean-centered anomaly R² relative to the *best previously established baseline*, RF with unsupervised target spectral z-standardization. Every date is one statistical observation, not each hexagon.
- Secondary: anomaly RMSE, 20% hotspot AUROC and Brier, absolute LST RMSE, residual Moran I, conformal coverage/width. No metric-driven choice of primary endpoint after seeing results.
- Paired exact sign-flip test (when tractable) plus date-level bootstrap 95% interval; 0.05 is descriptive, not a license for post-selection significance.

## Candidate methods, frozen settings

- Spectral NDVI/NDBI/MNDWI RF, 120 trees/min-leaf-5/max-features .8, seed 42; source-date centered target.
- Same RF with source and *unlabeled* target spectral z-scores.
- Source-only date-wise spectral normalization; source-only spatial residual climatology (mean residual for the same hexagon estimated from other source acquisitions, shrinkage 0.5, fallback zero); combined with z-standardized RF. The latter is **experimental**, not claimed novel by default.
- Source-only hotspot-frequency predictor, spectral RF classifier, and anomaly-score rank classifier for held-out hot-quintile outcome.
- Source-only meteorological date-baseline ridge compared with training-date mean, explicitly with retrospective ERA5 reanalysis and no target LST.

All target LST moments may be used to **define retrospective anomaly and percentile labels for scoring only**. Such labels are not operationally computable at inference. No target labels may enter feature transforms, model fitting, selection, residual corrections or calibration.

Hypotheses are evaluated as exploratory on the enlarged cohort because the initial six-date evidence preceded this freeze. No new method is named or claimed better until it wins date-level paired comparison against the strong baseline.

### Independent addition-only confirmation

**Before evaluating the newly acquired dates**, separately calculate the paired outcomes **on the additions only**, excluding all six Round-7 acquisition dates from the test statistic. The source training set for each new held date may contain all other dates (including the original six), but model specifications and selection are frozen here. Compare against *both* the previously strongest z-scored RF and the stronger six-date historical spatial-anomaly climatology. Use year-clustered inference in addition to per-date inference. The all-date analysis is descriptive; only addition-only outcomes can independently corroborate a model chosen after studying the original six.
