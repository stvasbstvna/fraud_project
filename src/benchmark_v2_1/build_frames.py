"""Quarantine and deduplicate historical synthetic candidates without endorsing labels."""
import json
from difflib import SequenceMatcher
from .core import DATA, RESULTS, FRAME_FIELDS, VARIANT_FIELDS, canonical_frames, defang, build_matrix, write_csv, write_json
import pandas as pd


def main():
    old=pd.read_csv(DATA/'full/semantic_frames.csv',keep_default_na=False)
    rows=[]
    for r in old.to_dict('records'):
        rows.append(dict(frame_id='',source_id='SYNTH-V21',source_row_id=r['frame_id'],
            source_dataset='legacy_researcher_authored_synthetic',source_url='internal',channel=r['channel'],
            language='en',true_label=r['label'],banking_related='yes',original_text=r['anchor_text'],
            defanged_text=defang(r['anchor_text']),entity=r['entity'],requested_action=r['requested_action'],
            intent=r['semantic_intent'],destination=r['destination'],contains_url='no',
            provenance_status='verified',license_status='verified',review_status='pending',
            notes='Candidate label/intent/action unvalidated; not eligible for generation or evaluation'))
    frames,duplicates=canonical_frames(pd.DataFrame(rows))
    write_csv(DATA/'source/frames.csv',frames.to_dict('records'),FRAME_FIELDS)
    write_csv(RESULTS/'diagnostics/exact_duplicates.csv',duplicates.to_dict('records'),list(duplicates.columns))
    # Surface similarity is a diagnostic, never an automatic equivalence judgment.
    near=[];records=frames.to_dict('records')
    for i,a in enumerate(records):
        for b in records[i+1:]:
            if a['entity'] != b['entity']:continue
            ratio=SequenceMatcher(None,a['defanged_text'].lower(),b['defanged_text'].lower(),autojunk=False).ratio()
            if ratio>=.90:near.append({'frame_id_a':a['frame_id'],'frame_id_b':b['frame_id'],'similarity':ratio})
    write_csv(RESULTS/'diagnostics/near_duplicates.csv',near,['frame_id_a','frame_id_b','similarity'])
    matrix=build_matrix(frames)
    write_csv(DATA/'generated/variant_matrix.csv',matrix,VARIANT_FIELDS)
    pilot=frames.groupby('true_label',group_keys=False).head(24)
    write_csv(DATA/'source/pilot_candidates.csv',pilot.to_dict('records'),FRAME_FIELDS)
    write_json(DATA/'source/build_summary.json',{'status':'CANDIDATES_PENDING_REVIEW',
        'input_rows':len(old),'unique_candidate_frames':len(frames),'duplicate_excess':len(duplicates),
        'candidate_labels':frames.true_label.value_counts().to_dict(),'eligible_frames':0,
        'candidate_condition_slots':len(matrix),'populated_C0':len(frames),'completed_C1_C6':0,
        'distinct_pilot_candidates':len(pilot),'near_duplicate_pairs_at_0_90':len(near),
        'near_duplicate_rule':'same entity; SequenceMatcher lowercased text >= 0.90; not automatic exclusion'})
    print(json.dumps({'candidate_frames':len(frames),'eligible_frames':0,'slots':len(matrix),'generated_rewrites':0}))


if __name__=='__main__':main()
