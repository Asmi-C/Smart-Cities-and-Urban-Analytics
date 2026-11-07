# Spatially cross-fitted, preference-robust intervention screening

**Scope.** The method identifies candidate *areas for further investigation*, not the causal effect or realized benefit of constructing an intervention.

Let hexagon i have remotely sensed land-surface temperature y_i, urban morphology x_i^m, satellite indices x_i^s, accessibility x_i^a and projected centroid location s_i.

## 1. Geographic generalization

We fit a family of predictors \(\hat f\) with input groups \(X=\{X^m,X^s,X^a\}\). For each outer spatial split \(k\), fit only on \(T_k\) and predict held-out \(V_k\):

\[\hat y_i=\hat f_{T_k}(x_i),\quad i\in V_k,\qquad RMSE=\sqrt{n^{-1}\sum_i(y_i-\hat y_i)^2}.\]

Compare random CV; 1, 1.5 and 2 km geographic blocks; contiguous x/y strips; and 250 m training exclusion buffers around held-out geographic blocks. Spatial KNN uses coordinates of training hexes only. Fixed random seeds and folds are explicit in code.

## 2. Residual structure and uncertainty

Using 8 spatial nearest neighbors (row-standardized weights), compute global residual Moran's I:

\[I=\frac{n}{S_0}\frac{\sum_{ij}w_{ij}e_ie_j}{\sum_i e_i^2},\qquad e_i=y_i-\hat y_i-\overline{(y-\hat y)}.\]

Permutation tests shuffle residual locations 999 times. A paired geographic-block bootstrap samples 1-km geographic groups with replacement and recomputes \(\Delta RMSE\) for fixed out-of-fold predictions. This does not capture full model-fitting variability.

For predictive intervals, partition the training blocks of each outer 1-km fold into fit and calibration groups; use the empirical high quantile \(q_{.9}\) of calibration absolute errors and interval \([\hat y_i-q,\hat y_i+q]\) on outer held-out groups. We measure empirical 90% target coverage. We **do not claim distribution-free coverage under spatial shift**.

## 3. Multiobjective severity and preference acceptability

For screening, define normalized concern vector

\[z_i=(\mathrm{scaled}(LST_i),1-\mathrm{scaled}(Access_i),1-\mathrm{scaled}(BlueGreen_i)).\]

These are indicators of *need*, not estimators of intervention effectiveness. The Pareto front contains units not jointly exceeded on all concern dimensions by any other unit. The front number identifies nondomination depth, not a unique optimum.

For each admissible preference weight \(w\in\Delta^2\), compute \(S_i(w)=w^T z_i\), descending rank \(r_i(w)\) (1 indicates greatest concern), and top-quintile acceptability

\[A_i=\frac{1}{B}\sum_{b=1}^B 1\{r_i(w_b)\le\lceil0.2n\rceil\}.\]

We report mean, median and standard deviation of ranks and normalized entropy of rank-decile occupancy. The 501 scenarios comprise equal weights plus 500 seeded Dirichlet(2,2,2) samples; these represent **hypothetical policy preferences, not a statistical prior inferred from planners**.

## 4. Confidence-aware classes

Retain two separate evidence dimensions: policy acceptability A_i and geographically cross-fitted heat interval width W_i. Report (A_i≥0.8) stable candidates with lower versus higher than median W_i. Units with 0.2≤A_i<0.8 remain preference-sensitive. Thresholds are decision scenarios, not validated clinical-style cutoffs. Do not combine disparate uncertainties into an apparently precise single number.

Intervention labels follow interpretable indicator rules and are explicitly called feasibility-evaluation candidates. Their effectiveness, cost and governance feasibility are unknown.

## Critical limitations

Some outcome labels and predictors are derived from related satellite imagery; downstream validation cannot establish independent temperature measurement accuracy. Indicators may be strongly correlated. Spatial grouping does not automatically solve temporal confounding. Weight scenarios are normative. No urban intervention effect has been measured.
