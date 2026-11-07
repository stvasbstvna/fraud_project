"""Final read-only research consistency audit and supplemental quality receipts."""
from .core import *
import math

def quality():
    baseline=csv_rows(ROOT/'docs/benchmark_v3/BASELINE_INVENTORY.csv')
    changed=[r['path'] for r in baseline if not (ROOT/r['path']).is_file() or file_sha(ROOT/r['path'])!=r['sha256']]
    if changed:raise ValueError('Historical baseline changed: '+str(changed))
    protected=csv_rows(DATA/'provenance/protected_inventory.csv')
    actual=set()
    for folder in ['data/benchmark_v3/final_run','models/benchmark_v3/final_run','results/benchmark_v3/final_run']:
        actual.update(p.relative_to(ROOT).as_posix() for p in (ROOT/folder).rglob('*') if p.is_file())
    actual.add('docs/benchmark_v3/FINAL_REPORT.md')
    if actual!={r['path'] for r in protected}:raise ValueError('Protected directory file list changed')
    verify_protected()
    manifest=read(RESULTS/'RUN_MANIFEST.json')
    for name,h in manifest['outputs'].items():
        if file_sha(ROOT/name)!=h:raise ValueError('Run output changed: '+name)
    index=csv_rows(RESULTS/'RESULT_EVIDENCE_INDEX.csv');tables={}
    if len({r['result_id'] for r in index})!=len(index):raise ValueError('Duplicate evidence index ID')
    for entry in index:
        path=ROOT/entry['source_file']
        if path not in tables:tables[path]=csv_rows(path)
        record,column=entry['source_columns'].split(';');record=int(record.split('=')[1])-2;column=column.split('=',1)[1]
        if tables[path][record][column]!=entry['value']:raise ValueError('Result index differs from exact source cell')
    primary=csv_rows(RESULTS/'statistics/primary_tests.csv')
    if len(primary)!=24 or any(int(r['N_frames'])!=0 or r['raw_p'] for r in primary):raise ValueError('Zero-complete primary test status inconsistent')
    metadata=list((RESULTS/'figures').glob('*_metadata.json'))
    for p in metadata:
        for suffix in ['_data.csv','.png','.svg']:
            q=p.with_name(p.name.replace('_metadata.json',suffix))
            if not q.is_file():raise ValueError('Missing figure sibling')
        meta=read(p)
        if 'primary_complete_case' in meta['filters'] and meta['N']['primary_complete_frames']!=0:raise ValueError('Primary figure support mismatch')
    summary=read(RESULTS/'SUMMARY.json')
    ledger=csv_rows(RESULTS/'PROMPT_LOG.csv')
    if len(ledger)!=summary['calls']['calls'] or len({r['call_id'] for r in ledger})!=len(ledger):raise ValueError('Prompt call ledger mismatch')
    receipt={'status':'PASSED_READ_ONLY_CONSISTENCY','baseline_historical_files':len(baseline),'baseline_files_changed':0,'protected_final_v3_files':len(protected),'protected_file_list_unchanged':True,'run_output_hashes_verified':len(manifest['outputs']),'evidence_index_cells_verified':len(index),'primary_tests_defined':0,'primary_tests_preregistered':24,'figure_bundles':len(metadata),'actual_call_rows':len(ledger),'modernbert_replay':read(RESULTS/'predictions/modernbert_replay.json'),'scientific_primary_status':summary['stats_status'],'clinical_or_deployment_validation':False}
    immutable_json(RESULTS/'QUALITY_VERIFICATION.json',receipt)
    files=[]
    for folder in ['configs','data','docs','models','results','src','tests']:
        base=ROOT/folder/'benchmark_v3_2'
        for p in base.rglob('*'):
            if not p.is_file() or '__pycache__' in p.parts or 'figure_pytest' in str(p) or 'ADDED_FILES' in p.name:continue
            files.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':file_sha(p)})
    files=sorted(files,key=lambda r:r['path'])
    # Inventory revisions are additive too; never overwrite an earlier snapshot.
    write_csv(DOCS/f'ADDED_FILES_{sha(canonical(files))[:12]}.csv',files)
    print(json.dumps(receipt,indent=2),flush=True)
    return receipt
if __name__=='__main__':quality()
