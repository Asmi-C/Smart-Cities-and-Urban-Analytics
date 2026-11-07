# Round-10 primary endpoint and selection guard

**Primary descriptive endpoint:** loss in held-out anomaly R² moving from D2 (new date, familiar geography) to D3 (new date and unseen geography), for each fixed model family. The central scientific claim is *evaluation optimism / rank reversal*, not superior hybrid prediction.

Freeze: 15 existing Landsat-8 dates, three normalized optical indices, four fixed models, median-centroid quadrant IDs, 15 minimum target units, fixed seeds, per-date temporal holdout, and macro-mean per evaluation domain. Use no test LST in feature creation, scaling, spatial lag or correction. Target date LST mean is evaluation-only. Determine if model ranking reverses using Kendall and Spearman on four models.

**Confirmatory gate:** all 15 existing dates are development data and cannot serve as untouched confirmation. Before claims of confirmed generalization, acquire independent Landsat 8/9 acquisitions or a second area under frozen scene metadata/QA/split rules, and evaluate once with no post-test tuning.
