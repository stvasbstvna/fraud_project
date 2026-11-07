"""Objective validation only. Never assigns human semantic approval."""
import argparse
from pathlib import Path
import pandas as pd
from .core import DATA, RESULTS, validate_variant, write_csv


def main():
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,default=DATA/'generated/variant_matrix.csv');a=p.parse_args()
    rows=pd.read_csv(a.input,keep_default_na=False).to_dict('records')
    out=[{'variant_id':r['variant_id'],'generation_status':r['generation_status'],
          'objective_errors':';'.join(validate_variant(r)) if r['variant_text'] else 'NOT_GENERATED',
          'human_review_status':'pending'} for r in rows]
    write_csv(RESULTS/'diagnostics/variant_validation.csv',out,list(out[0]) if out else ['variant_id','objective_errors'])
    print(f'{len(out)} slots checked; no human approvals assigned')


if __name__=='__main__':main()
