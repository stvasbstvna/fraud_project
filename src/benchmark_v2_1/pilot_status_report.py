"""Report actual pilot candidate composition and unexecuted scientific outputs."""
import json
import pandas as pd
from .core import DATA,RESULTS,write_csv,write_json

TABLES={
 'B_manipulation_check':['condition','N','jaccard_similarity','normalized_edit_distance','tfidf_cosine_similarity','surface_distance','human_approval_rate'],
 'C_detector_performance':['condition','lr_accuracy','lr_recall','lr_fnr','lr_fpr','rf_accuracy','rf_recall','rf_fnr','rf_fpr'],
 'D_probability_movement':['condition','lr_mean_delta','lr_median_delta','lr_ci95_low','lr_ci95_high','rf_mean_delta','rf_median_delta','rf_ci95_low','rf_ci95_high'],
 'E_decision_transitions':['condition','lr_detected_to_missed','lr_missed_to_detected','lr_legitimate_to_fp','lr_fp_to_legitimate','rf_detected_to_missed','rf_missed_to_detected','rf_legitimate_to_fp','rf_fp_to_legitimate'],
 'F_largest_absolute_changes':['frame_id','condition','label','model','original_score','rewritten_score','absolute_change','transition'],
 'qualitative_prompt_example':['condition','prompt_goal','resulting_text','key_linguistic_change','lr_score','rf_score'],
}


def main():
    f=pd.read_csv(DATA/'source/pilot_48_candidates.csv',keep_default_na=False)
    group=['source_id','candidate_label','intent_category','entity','template_family_id']
    table=f.groupby(group,dropna=False).size().reset_index(name='count')
    table['status']='candidate_only_source_review_pending'
    path=RESULTS/'tables/pilot_48/A_pilot_composition.csv'
    write_csv(path,table.to_dict('records'),list(table.columns))
    columns=list(table.columns)
    with path.with_suffix('.md').open('x',encoding='utf-8') as handle:
        handle.write('# Proposed pilot composition — not validated ground truth\n\n')
        handle.write('| '+' | '.join(columns)+' |\n| '+' | '.join(['---']*len(columns))+' |\n')
        for row in table.to_dict('records'):handle.write('| '+' | '.join(str(row[c]) for c in columns)+' |\n')
    for name,fields in TABLES.items():
        write_csv(RESULTS/f'tables/pilot_48/{name}.csv',[],fields)
    write_json(RESULTS/'tables/pilot_48/table_status.json',{
        'A':'OBSERVED_CANDIDATE_COMPOSITION_ONLY','B_F':'NOT RUN','qualitative_prompt_example':'NOT AVAILABLE',
        'reason':'No source-approved cohort, generated rewrites, human-approved variants or frozen predictions',
        'candidate_source_texts':len(f),'generated_condition_rows':0,'complete_case_frames':0,'final_condition_rows':0})
    figures={
        'Figure 1':{'x':'C0–C6','y':'recall 0–1','marks':'LR/RF lines','not_conclude':'No measured condition effect exists yet'},
        'Figure 2':{'x':'C1–C6','y':'P(C0)−P(Ci)','marks':'paired means/medians and frame bootstrap uncertainty','not_conclude':'No decline or improvement has been established'},
        'Figure 3':{'x':'prespecified surface distance','y':'signed/absolute paired score change','marks':'one variant per point; LR and RF separate','not_conclude':'Association would not establish lexical causality'},
        'Figure 4':{'x':'condition','y':'four decision-transition types','marks':'count heatmaps by model','not_conclude':'Do not ignore reverse transitions or legitimate false positives'},
        'Figure 5':{'x':'C0–C6','y':'phishing probability 0–1','marks':'LR/RF lines, threshold .5; median-movement frame, deterministic tie break','not_conclude':'Do not select the most dramatic frame or call largest change representative'},
    }
    write_json(RESULTS/'figures/pilot_48_figure_status.json',{'status':'NOT RUN','reason':'PILOT NOT READY','planned_core_figures':figures})
    print(json.dumps({'candidate_composition_rows':len(table),'empirical_performance_tables':0,'scientific_figures':0}))


if __name__=='__main__':main()
