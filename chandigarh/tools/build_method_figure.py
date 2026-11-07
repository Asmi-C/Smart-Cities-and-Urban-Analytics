"""Draw the conceptual pipeline as a publication-friendly vector PDF and PNG."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

root=Path(__file__).resolve().parents[1]; dest=root/'paper/figures';dest.mkdir(parents=True,exist_ok=True)
fig,ax=plt.subplots(figsize=(12,7.1));ax.set(xlim=(0,12),ylim=(0,7.1));ax.axis('off')
def box(x,y,w,h,t,color):
    patch=FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.13,rounding_size=0.12',facecolor=color,edgecolor='#234456',linewidth=1.2)
    ax.add_patch(patch);ax.text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=12,color='#0f2e3a',weight='semibold')
def arrow(a,b):ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=14,lw=1.5,color='#537a88'))
box(4,6.12,4,.68,'Satellite + OSM + demographic proxies','#b9e2df')
arrow((6,6.1),(6,5.75));box(4,5.1,4,.65,'Spatial harmonization / 537 hexes','#dbeef3')
arrow((6,5.08),(6,4.75))
for x,t in [(1,'Morphology'),(4.5,'Spectral / heat'),(8,'Service access')]:box(x,3.95,3,.6,t,'#d8e9ec')
for x in (2.5,6,9.5):arrow((6,4.75),(x,4.58));arrow((x,4.57),(x,4.59))
box(1,2.65,4.2,.73,'Predictive models + spatial CV','#c3dbf0')
box(6.8,2.65,4.2,.73,'Pareto fronts + preference ranks','#f2d6bc')
for x in (2.5,6,9.5):arrow((x,3.94),(3.1 if x<6 else 8.9,3.4))
box(1,1.35,4.2,.73,'Residual tests + spatial intervals','#c3dbf0')
box(6.8,1.35,4.2,.73,'Rank acceptance / uncertainty','#f2d6bc')
arrow((3.1,2.62),(3.1,2.1));arrow((8.9,2.62),(8.9,2.1))
box(3.2,.13,5.6,.73,'Transparent intervention candidates','#b9e2df')
arrow((3.1,1.32),(5,.85));arrow((8.9,1.32),(7,.85))
fig.tight_layout();fig.savefig(dest/'method_framework.png',dpi=200);fig.savefig(dest/'method_framework.pdf');plt.close(fig)
