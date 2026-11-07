"""Frozen source/configuration bindings required before fitting or scoring."""
from .core import DATA, CONFIG, read_json, verify_hash


def check_protocol_hashes(freeze, paths):
    for key,path in paths.items():verify_hash(path,freeze[key])


def verify_frozen_inputs(experiment='primary'):
    freeze=read_json(DATA/'frozen/cohort_manifest.json')
    if not freeze['status'].startswith('FROZEN_'):raise ValueError('Accepted source freeze required')
    check_protocol_hashes(freeze,{'protocol_sha256':CONFIG/'experiment_protocol.json',
        'source_review_protocol_sha256':CONFIG/'source_review_v3_1.json',
        'source_registry_sha256':DATA/'provenance/source_registry.csv'})
    if 'correction_plan_sha256' in freeze:
        check_protocol_hashes(freeze,{'correction_plan_sha256':CONFIG/'template_correction_v3_2.json'})
    if 'final_eligibility_plan_sha256' in freeze:
        check_protocol_hashes(freeze,{'final_eligibility_plan_sha256':CONFIG/'final_eligibility_plan.json',
              'final_eligibility_decisions_sha256':DATA.parent/'final_eligibility_audit/final_decisions.json'})
    name,key=('modeling_cohort.csv','cohort_sha256') if experiment=='primary' else ('source_holdout_cohort.csv','source_holdout_cohort_sha256')
    verify_hash(DATA/'frozen'/name,freeze[key])
    return freeze
