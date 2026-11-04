"""Create a standalone, editable PowerPoint from verified analysis outputs."""
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

R=Path(__file__).resolve().parents[1]
prs=Presentation();prs.slide_width=Inches(13.333);prs.slide_height=Inches(7.5)
NAVY=RGBColor(12,34,54);TEAL=RGBColor(21,150,148);WHITE=RGBColor(248,251,253);MUTED=RGBColor(171,199,210)

def txt(slide,text,x,y,w,h,size=22,color=WHITE,bold=False):
    sh=slide.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h))
    tf=sh.text_frame;tf.word_wrap=True
    for k,line in enumerate(text.split('\n')):
        p=tf.paragraphs[0] if k==0 else tf.add_paragraph()
        p.text=line;p.font.size=Pt(size);p.font.name='Aptos';p.font.bold=bold;p.font.color.rgb=color;p.space_after=Pt(12)
    return sh

def slide(title,subtitle=None):
    s=prs.slides.add_slide(prs.slide_layouts[6]);s.background.fill.solid();s.background.fill.fore_color.rgb=NAVY
    bar=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(.6),Inches(.65),Inches(.12),Inches(.52));bar.fill.solid();bar.fill.fore_color.rgb=TEAL;bar.line.fill.background()
    txt(s,title,.88,.57,11.8,.9,31,bold=True)
    if subtitle:txt(s,subtitle,.88,1.47,11.7,.5,15,MUTED)
    txt(s,f'{len(prs.slides):02}',12.45,7.05,.4,.25,10,MUTED)
    return s

def body(title,points,subtitle=None):
    s=slide(title,subtitle);txt(s,'\n'.join('•  '+a for a in points),1,2.15,11.4,4.45,23)
    return s

def pic(title,path,caption=None):
    s=slide(title,caption)
    from PIL import Image
    im=Image.open(path);iw,ih=im.size
    box=(.92,1.9,11.5,4.95);scale=min(box[2]/iw,box[3]/ih)
    w,h=iw*scale,ih*scale
    s.shapes.add_picture(str(path),Inches(box[0]+(box[2]-w)/2),Inches(box[1]+(box[3]-h)/2),width=Inches(w),height=Inches(h))
    return s

s=slide('Where can New Town intervene with confidence?','Spatially validated urban heat modelling and priority stability | NKDA, Kolkata')
txt(s,'A research prototype built on the existing smart-city GIS pipeline',1.0,2.6,11.3,1.2,30)
txt(s,'537 hexagons   ·   5-fold geographic validation   ·   302 weighting scenarios',1.05,4.95,10.9,.9,21,RGBColor(75,205,197))
body('Research problem',[
    'Local surface-heat and service-access patterns vary within the planned township.',
    'Neighboring spatial units share information: random validation can overstate transferable model skill.',
    'A single weighted liveability score conceals sensitivity to planning preferences.'])
body('What the literature already covers',[
    'A 2024 New Town study quantifies historical land-cover transitions and associated heat.',
    'A 2024 Rajarhat study investigates greenery, waterscapes and urban heat.',
    'Roberts et al. (2017) explain why structured cross-validation matters for spatial data.',
    'Our focus: test geographic generalization and stability of intervention rankings.'],
    'Literature is context and methodological grounding, not a directly comparable leaderboard.')
body('Research questions and contributions',[
    'RQ1  How much does random splitting understate geographically held-out error?',
    'RQ2  Which urban-feature groups help explain satellite-derived LST across blocks?',
    'RQ3  Which low-liveability zones survive changes in indicator weights?',
    'Deliverables: model comparisons, ablation, georeferenced priority stability.'])
pic('Study area: existing analysis units',R/'outputs/figures/01_study_area.png','NKDA boundary digitized from planning sheet; existing 250-m hexagonal analysis')
body('Executed methodology',[
    '537 NKDA hexagons with Landsat LST, satellite indices, morphology and OSM service distances.',
    'Mean, Ridge, Random Forest, gradient boosting; 4 feature groups.',
    'Random 5-fold versus 5-fold GroupKFold on 52 fixed 1-km geographic blocks.',
    'Lowest liveability quintile across AHP, equal and 300 seeded weight perturbations.'])
pic('Existing surface heat pattern',R/'outputs/figures/05_lst.png','Descriptive satellite-derived land-surface temperature; not ambient air exposure')
pic('Spatial CV exposes optimistic random-split estimates',R/'outputs/PPT_FIGURES/01_spatial_cv.png','Combined-feature RF: random 0.726°C vs spatial 0.876°C RMSE')
pic('Ablation reveals no combined-model gain',R/'outputs/PPT_FIGURES/02_ablation.png','Morphology-only RF spatial RMSE 0.875°C; combined RF 0.876°C')
pic('Geographically held-out predictions',R/'outputs/PPT_FIGURES/04_predicted_vs_observed.png','Combined Random Forest: out-of-fold spatial R² = 0.527')
pic('Intervention priorities and their stability',R/'outputs/PPT_FIGURES/03_intervention_map.png','79 hexes remain bottom quintile in ≥80% of 302 weight scenarios; action categories are heuristic')
body('Quantitative conclusions',[
    'Spatial holdout increases combined RF RMSE by 0.150°C (20.7%) relative to random CV.',
    'Morphology-only RF marginally beats combined RF under spatial holdout.',
    '79 of 537 hexes are persistently low-ranked across ≥80% of weighting scenarios.',
    'AHP/equal weights share 74 of 108 AHP-priority hexes (rank Spearman ρ = 0.857).'])
body('Validation caveats matter',[
    'Original LULC maps show poor independent agreement: 21.21% (2016 Dynamic World); 43.79% (2021 ESA).',
    'The original time series uses 2016 top-of-atmosphere and later surface-reflectance composites.',
    'Satellite LST does not directly measure human heat stress or establish causal effects.',
    'OSM completeness, independent labels and intervention success require further testing.'])
body('Next experiments toward submission',[
    'Repair and independently validate LULC inputs; harmonize sensors and seasonal imagery.',
    'Repeat spatial CV across block sizes, buffer distances and temporal holdouts.',
    'Test residual spatial autocorrelation and uncertainty; audit OSM service coverage.',
    'Validate decision rules with local planning evidence and replicate in another township.'])
body('Takeaway',[
    'We extended an operational NKDA GIS project with executed spatial model evaluation.',
    'The evaluation finds a meaningful random-versus-spatial validation gap.',
    'Robust priority mapping offers a transparent starting point for planning discussions.',
    'The prototype supports a research narrative, with independent validation still necessary.'])
out=R/'ppt/NKDA_GeoAI_Research_Presentation.pptx';prs.save(out)
print(out, len(prs.slides))
