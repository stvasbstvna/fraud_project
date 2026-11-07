"""Prepare an explicit Git publication allowlist without modifying research evidence."""
from pathlib import Path
import subprocess
import json
import csv
import io
import re
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.git/publication';OUT.mkdir(exist_ok=True)
EXCLUDED_PARTS={'.git','__pycache__','.pytest_cache','.venv','.venv-benchmark-v3','external','node_modules','.ipynb_checkpoints'}
SECRET=re.compile(rb'(?:sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{24,}|gh[pousr]_[A-Za-z0-9]{24,}|github_pat_[A-Za-z0-9_]{40,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|AKIA[0-9A-Z]{16})')
TEXT_FIELDS=re.compile(r'(^|_)(text|message|sms|rewritten|rewrite|utterance|content)($|_)',re.I)

def git(*args):return subprocess.check_output(['git','-c','core.quotepath=false',*args],cwd=ROOT,stderr=subprocess.DEVNULL)
def ignored(p):
    parts=p.relative_to(ROOT).parts
    return bool(set(parts)&EXCLUDED_PARTS or any(x.startswith(('.test_tmp','test_','cache_guard','figure_pytest')) for x in parts[:-1]) or p.suffix.lower() in {'.joblib','.safetensors','.bin','.pt','.pth','.pyc','.pkl','.zip','.xlsx','.xls','.html','.htm','.pdf'} or p.name.startswith('.env') or p.suffix=='.env' or p.name=='tokenizer.json' or 'modernbert_base_source' in parts or 'sting9' in parts)

def main():
    tracked={p.decode('utf-8') for p in git('ls-files','-z').split(b'\0') if p}
    chosen={ROOT/p for p in tracked if (ROOT/p).is_file()};excluded=[]
    for folder in ['src','configs','docs','tests','results','schemas','prompts','scripts','analysis','models','data/benchmark_v3','data/benchmark_v3_2']:
        base=ROOT/folder
        if not base.exists():continue
        for p in base.rglob('*'):
            if not p.is_file():continue
            rel=p.relative_to(ROOT).as_posix()
            if ignored(p):excluded.append((rel,'local/cache/binary/archive/upstream snapshot'));continue
            if folder=='models' and p.suffix.lower() not in {'.json','.txt','.md','.csv'}:excluded.append((rel,'model metadata only'));continue
            if p.stat().st_size>45*1024*1024:excluded.append((rel,'large artifact'));continue
            # Existing v3/v3.2 pools have separately documented accepted source rights.
            known_rights='/benchmark_v3/' in '/'+rel or '/benchmark_v3_2/' in '/'+rel
            if not known_rights and folder=='results':
                if p.suffix.lower()=='.csv':
                    with p.open(encoding='utf-8-sig',errors='replace',newline='') as f:header=next(csv.reader(f),[])
                    if any(TEXT_FIELDS.search(c) for c in header):excluded.append((rel,'historical row-level text; redistribution rights not established'));continue
                if p.suffix.lower()=='.json' and re.search(r'"(?:safe_text|text|message|original_text|rewritten_text|variant_text)"\s*:',p.read_text(encoding='utf-8',errors='replace')):excluded.append((rel,'historical JSON text payload'));continue
            chosen.add(p)
    for name in ['.gitattributes','.gitignore','README.md','requirements.txt','environment-lock.txt','pytest.ini','PUBLISHING.md','BENCHMARK_RESULTS.md','data/ATTRIBUTION.md','data/README.md','data/final/README.md','data/final/dataset_summary.csv']:
        p=ROOT/name
        if p.is_file():chosen.add(p)
    findings=[]
    for p in sorted(chosen):
        if SECRET.search(p.read_bytes()):findings.append(p.relative_to(ROOT).as_posix())
    if findings:
        print(json.dumps({'secret_like_files':findings,'values_not_printed':True},indent=2));raise SystemExit(1)
    paths=[p.relative_to(ROOT).as_posix() for p in sorted(chosen)]
    (OUT/'paths.nul').write_bytes(b'\0'.join(p.encode('utf-8') for p in paths)+b'\0')
    with (OUT/'excluded.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f);w.writerow(['path','reason']);w.writerows(excluded)
    report={'files':len(paths),'bytes':sum(p.stat().st_size for p in chosen),'top_level_counts':dict(Counter(p.split('/')[0] for p in paths)),'excluded_candidates':len(excluded),'secret_findings':0,'largest':[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size} for p in sorted(chosen,key=lambda p:p.stat().st_size,reverse=True)[:12]],'pathspec_file':'.git/publication/paths.nul'}
    (OUT/'summary.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
