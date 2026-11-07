"""Inspect the versioned source registry; no download or automatic label mapping."""
from .core import CONFIG, DATA, write_json
import pandas as pd


def main():
    registry=pd.read_csv(CONFIG/'source_registry.csv',keep_default_na=False)
    required='source_id aggregator original_dataset original_url channel language label_schema license_status redistribution_allowed candidate_use notes'.split()
    if set(required)-set(registry):raise ValueError('Incomplete source registry')
    if registry.source_id.duplicated().any():raise ValueError('Duplicate source IDs')
    write_json(DATA/'source/source_audit.json',{'status':'ROW_LEVEL_EXTERNAL_SOURCE_REVIEW_PENDING',
        'sources_evaluated':len(registry),'external_sources_accepted_for_generation':0,
        'rows_imported_from_SMISH_DT':0,'registry':str(CONFIG/'source_registry.csv')})
    print(f'{len(registry)} source entries; 0 external sources accepted for generation')


if __name__=='__main__':main()
