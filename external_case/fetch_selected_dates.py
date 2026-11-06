"""Acquire all preselected STAC dates; reuse verified COG cache.

Run AFTER `discover_dates.py`; scene choice never reads prediction scores.
"""
from pathlib import Path
import os,sys,pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent))
from temporal_landsat import extract
R=Path(__file__).resolve().parents[1]
sel=pd.read_csv(R/os.environ.get('NKDA_SELECTION_FILE','data/selected_acquisitions.csv'))
for item in sel.item_id:
    output=R/f'external_case/data/landsat_hex_{item[:4]}_{item.split("_")[3]}.csv'
    if output.exists():
        print('Using existing harmonized acquisition',item,flush=True)
    else:
        print('Downloading selected acquisition',item,flush=True)
        df,metadata=extract(item)
        print('Complete',item,'valid LST hexes',int(df.LST.notna().sum()),flush=True)
