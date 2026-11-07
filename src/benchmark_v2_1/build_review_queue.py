"""Create detector-blinded, content-bound review forms; two reviewers per available text."""
import argparse
from pathlib import Path
import pandas as pd
from .core import DATA, REVIEW_FIELDS, digest, write_csv, write_json


def main():
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,default=DATA/'generated/variant_matrix.csv');a=p.parse_args()
    rows=pd.read_csv(a.input,keep_default_na=False).to_dict('records');queue=[]
    for r in rows:
        if not r['variant_text']:continue
        for slot in (1,2):
            queue.append({**{k:r[k] for k in ['frame_id','variant_id','condition','true_label','entity','requested_action','intent','destination','defanged_text','variant_text']},
                'text_sha256':digest(r['variant_text']),'reviewer_slot':slot,'reviewer':'','decision':'pending',
                **dict.fromkeys(REVIEW_FIELDS,''),'directness_rating':'','review_notes':''})
    fields=list(queue[0]) if queue else ['variant_id','text_sha256','reviewer','decision',*REVIEW_FIELDS,'review_notes']
    write_csv(DATA/'review/review_queue.csv',queue,fields)
    write_csv(DATA/'review/adjudication.csv',[],['variant_id','text_sha256','adjudicator','decision','reason'])
    write_json(DATA/'review/review_summary.json',{'available_texts':len(queue)//2,'review_assignments':len(queue),
        'approved_variants':0,'rejected_variants':0,'needs_adjudication':0,'pending_variants':len(queue)//2,
        'generated_rewrite_reviews':0,'agreement':'NOT AVAILABLE','status':'PENDING_HUMAN_REVIEW'})
    print(f'{len(queue)} blank independent review assignments; 0 approvals')


if __name__=='__main__':main()
