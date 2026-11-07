"""Revise the baseline talk with executed, evidence-based research experiments."""
from pathlib import Path
import runpy
ns=runpy.run_path(str(Path(__file__).with_name('build_ppt.py')))
prs=ns['prs'];slide=ns['slide'];body=ns['body'];pic=ns['pic'];txt=ns['txt'];R=ns['R']

# Keep introduction and original satellite heat context (first seven slides).
# Remove outdated result claims and replace them with re-run advanced experiments.
for index in reversed(range(7,len(prs.slides))):
    el=prs.slides._sldIdLst[index]
    prs.part.drop_rel(el.rId);prs.slides._sldIdLst.remove(el)
for s in prs.slides:
    for shape in s.shapes:
        if shape.has_text_frame:
            for paragraph in shape.text_frame.paragraphs:
                for run in paragraph.runs:
                    run.text=run.text.replace('302 weighting scenarios','501 weighting scenarios').replace('302 weight','501 weight')

pic('Proposed research framework',R/'paper/figures/method_framework.png',
    'Two complementary outputs: geographically validated heat estimates and preference-aware decision screening')

pic('Geographic independence changes error',R/'outputs/PPT_FIGURES/05_geographic_stress_test.png',
    'Eight validation designs. Split geometry matters; larger blocks do not guarantee monotonic error.')
body('Research results: geographic validation',[
    'Random 5-fold RF RMSE 0.725°C, 1-km block RMSE 0.891°C.',
    '2-km blocks + 250-m exclusion buffer: RMSE 0.954°C.',
    'Coordinate-only SpatialKNN8 under 1-km blocks: RMSE 1.241°C.',
    'Contiguous geographic holdouts reveal distinct model difficulty across the township.'])
pic('Additional features do not consistently help',R/'outputs/PPT_FIGURES/06_nested_ablation.png',
    '1-km block validation for matched RF feature families')
body('Statistical comparison of feature families',[
    'Combined minus morphology RF RMSE: +0.016°C.',
    'Paired 1-km geographic-block bootstrap 95% interval: [−0.092, +0.164]°C.',
    'The interval includes zero: no evidence of combined-model superiority.',
    'Negative ablation results are reported without selecting favorable folds.'])
body('Residual spatial dependence remains',[
    '1-km block residual Moran’s I: RF 0.439, HGB 0.422, Ridge 0.496.',
    'SpatialKNN8 residual Moran’s I: 0.345.',
    'All permutation p-values = 0.001 (999 permutations).',
    'Spatially structured errors remain a major unresolved paper weakness.'])
body('Prediction uncertainty: empirical check',[
    'Nominal 90% intervals calibrated using separate geographic training blocks.',
    'Observed out-of-fold interval coverage: 91.4%.',
    'Mean interval width: 2.930°C.',
    'This is descriptive coverage and does not guarantee transfer under spatial shift.'])
pic('Pareto trade-offs and rank acceptability',R/'outputs/PPT_FIGURES/07_rank_pareto_uncertainty.png',
    'Each map represents a distinct notion of urban concern or evidence uncertainty')
body('Proposed decision-screening protocol',[
    'Three objectives: heat severity, service-access deficit and blue-green deficit.',
    'Pareto fronts retain trade-offs; 501 weighting scenarios yield rank distributions.',
    '58 hexes are top-quintile candidates in ≥80% of weighting scenarios.',
    '37 of those have lower-than-median heat prediction interval widths.'])
body('Evidence boundaries and next experiments',[
    'The original LULC maps require harmonized reprocessing and independent labels.',
    'Residual Moran I is significant; spatial process modelling remains necessary.',
    'Validate OSM coverage, resident exposure, and feasible intervention locations.',
    'Next: temporal and external-city transfer, stakeholder preference elicitation.'])
body('Conclusion: a stronger but still provisional study',[
    'Geographic validation substantially changes apparent heat-model skill.',
    'Additional data families do not yet demonstrate reliable incremental benefit.',
    'Pareto severity, policy preference stability and prediction uncertainty remain distinct.',
    'A credible research protocol is implemented; independent validation is required before submission.'])
out=R/'ppt/NKDA_IEEE_Research_Revised.pptx';prs.save(out)
print('Revised',len(prs.slides),out)
