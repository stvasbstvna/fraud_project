"""Export source-review forms or import genuine independent source decisions."""
import argparse
from pathlib import Path
import pandas as pd
from .core import DATA,FRAME_FIELDS,REVIEW_FIELDS,source_digest,verify_source_reviews,write_csv


def import_reviews(frames,reviews):
    result=[]
    for row in frames.to_dict('records'):
        candidate={**row,'review_status':'approved'}
        try:verify_source_reviews([candidate],reviews)
        except ValueError:candidate['review_status']='pending'
        result.append(candidate)
    return pd.DataFrame(result,columns=FRAME_FIELDS)


def main():
    p=argparse.ArgumentParser();p.add_argument('--reviews',type=Path);a=p.parse_args()
    frames=pd.read_csv(DATA/'source/frames.csv',keep_default_na=False)
    if a.reviews:
        imported=import_reviews(frames,pd.read_csv(a.reviews,keep_default_na=False).to_dict('records'))
        write_csv(DATA/'source/frames_reviewed.csv',imported.to_dict('records'),FRAME_FIELDS)
        print(f'{int(imported.review_status.eq("approved").sum())} sources have independent human approval');return
    queue=[]
    for row in frames.to_dict('records'):
        for slot in (1,2):queue.append({**row,'source_sha256':source_digest(row),'reviewer_slot':slot,
            'reviewer':'','decision':'pending',**dict.fromkeys(REVIEW_FIELDS,''),'review_notes':''})
    write_csv(DATA/'review/source_review_queue.csv',queue,list(queue[0]) if queue else FRAME_FIELDS)
    print(f'{len(queue)} source review assignments created; no approval assigned')


if __name__=='__main__':main()
