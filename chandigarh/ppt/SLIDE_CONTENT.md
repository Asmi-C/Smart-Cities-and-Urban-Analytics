# Research-talk text

## Problem
Urban heat and uneven walking access co-occur in a fast-changing planned township; a useful planning tool must show both predictive generalization and which target zones remain stable under preference changes.

## Gap
Existing local literature already maps LULC and UHI. Conventional random splits may produce optimistic spatial model accuracy; single weighted indices conceal subjective weights.

## Questions
RQ1: How much does random validation overestimate NKDA heat-model skill? RQ2: Which feature groups generalize across geographic blocks? RQ3: Which low-liveability areas are stable across weighting choices?

## Method
537 existing 250-m hexes. Predict pre-monsoon satellite LST from morphology, spectral indices and service distance. Compare four models and random vs 1-km block 5-fold CV. Stress-test bottom-quintile indices over 302 weight schemes.

## Results
RF combined model: random RMSE 0.726°C vs spatial RMSE 0.876°C; spatial R² 0.527. Morphology-only spatial RMSE 0.875°C, which **slightly outperforms** the combined model; therefore no integration lift is established. 79 hexes remain lowest-quintile under at least 80% of weights.

## Limitation
Satellite-temperature prediction is neither causation nor independently measured human exposure. Temporal LULC map agreement requires repair. Intervention advice needs field validation.
