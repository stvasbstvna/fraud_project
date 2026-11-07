"""Assemble C0 and accepted responses without inventing missing variants."""
import argparse
from pathlib import Path
import pandas as pd
from .core import DATA,VARIANT_FIELDS,build_matrix,validate_matrix,write_csv


def assemble(frames,responses):
    baseline=[r for r in build_matrix(frames) if r['condition']=='C0']
    if any(r['condition']=='C0' for r in responses):raise ValueError('Responses must not replace C0')
    result=baseline+responses
    validate_matrix(result)
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--frames',type=Path,required=True);p.add_argument('--responses',type=Path,required=True)
    p.add_argument('--output',type=Path,default=DATA/'generated/complete_matrix.csv');a=p.parse_args()
    rows=assemble(pd.read_csv(a.frames,keep_default_na=False),pd.read_csv(a.responses,keep_default_na=False).to_dict('records'))
    write_csv(a.output,rows,VARIANT_FIELDS);print(f'{len(rows)} complete matrix rows assembled; not human-approved or frozen')


if __name__=='__main__':main()
