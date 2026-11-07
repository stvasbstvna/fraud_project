"""Publish explicitly unrun result schemas and actual source audit summaries."""
import json
import pandas as pd
from .source_audit import DATA, RESULTS, save_csv, save_json, save_bytes
from .verify import verify


def main():
    verify()
    schemas = [
        ('01_final_source_cohort', ['source', 'label', 'N', 'real_vs_synthetic', 'template_families']),
        ('02_message_function_distribution', ['label', 'message_function', 'N']),
        ('03_condition_eligibility', ['condition', 'eligible', 'ineligible', 'reason']),
        ('04_generation_review_attrition', ['condition', 'eligible', 'generated', 'retry', 'approved', 'rejected', 'approval_rate']),
        ('05_manipulation_validation', ['condition', 'N', 'token_jaccard', 'normalized_edit_distance', 'tfidf_cosine_similarity', 'structural_change']),
        ('06_main_detector_performance', ['model', 'condition', 'N', 'recall', 'FNR', 'FPR', 'accuracy']),
        ('07_probability_changes', ['model', 'label', 'condition', 'paired_N', 'signed_delta', 'absolute_delta', 'ci_low', 'ci_high']),
        ('08_decision_transitions', ['model', 'label', 'condition', 'paired_N', 'negative_to_positive', 'positive_to_negative']),
        ('09_legitimate_false_positives', ['model', 'condition', 'N', 'already_FP_at_C0', 'new_FP', 'recovered_FP', 'FPR']),
        ('10_distance_association', ['model', 'label', 'distance_metric', 'frame_N', 'effect', 'uncertainty', 'analysis_type']),
        ('11_model_comparison', ['condition', 'frame_N', 'LR_change', 'RF_change', 'paired_difference', 'movement_correlation']),
        ('12_extreme_cases', ['frame_id', 'label', 'condition', 'model', 'original_probability', 'variant_probability', 'absolute_delta', 'selection'])]
    statuses = []
    for name, fields in schemas:
        path = RESULTS / 'tables' / f'Table{name}.csv'
        save_csv(path, [], fields)
        save_bytes(path.with_suffix('.md'), (f'# Table {name.replace("_", " ")}\n\n**NOT RUN — source cohort insufficient.**\n\nNo empirical rows. The CSV contains the declared schema only; no zero rates or synthetic observations were substituted.\n\nV2.2 performed deterministic source feasibility checks, not independent human annotation or completed machine semantic review.\n').encode())
        statuses.append({'table': name, 'status': 'NOT RUN_SOURCE_COHORT_INSUFFICIENT', 'empirical_rows': 0})
    save_csv(RESULTS / 'tables/table_status.csv', statuses)
    rows = pd.read_csv(DATA / 'source/candidate_audit.csv', keep_default_na=False, low_memory=False)
    clear = rows[rows.candidate_label.eq('legitimate') & rows.rule_errors.eq('')]
    lineage = clear.groupby(['source_id', 'source_group']).agg(candidate_rows=('frame_id', 'size'), candidate_families=('template_family_id', 'nunique')).reset_index()
    save_csv(RESULTS / 'tables/Audit_control_lineage.csv', lineage.to_dict('records'))
    summary = json.loads((RESULTS / 'source_summary.json').read_text())
    save_csv(RESULTS / 'tables/Audit_capacity.csv', [{'distinct_candidate_control_families': summary['capacity_bound']['real_legitimate_candidate_families'],
             'optimistic_control_capacity_after_source_cap': summary['capacity_bound']['maximum_legitimate_before_semantic_review'],
             'required_minimum': 16, 'approved_source_frames': 0, 'generation_calls': 0, 'detector_predictions': 0}])
    save_json(RESULTS / 'figures/figure_status.json', {'status': 'NOT GENERATED_SOURCE_COHORT_INSUFFICIENT',
        'scientific_figures': 0, 'figures': [{'number': i, 'status': 'NOT AVAILABLE', 'reason': 'No accepted source cohort or frozen predictions'} for i in range(1, 8)],
        'independent_human_annotation': False})
    print('12 result schemas marked NOT RUN; 2 source-audit tables; 0 scientific figures')


if __name__ == '__main__': main()
