"""Separate automated branch. Human-review commands and evidence remain untouched."""
import argparse
import json
from .automated_protocol import initialize,AUTO_RESULTS


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--review-mode',choices=['automated'],required=True)
    p.add_argument('--stage',choices=['all','sources','generation','diagnostics','reports','verify'],default='all')
    p.add_argument('--offline',action='store_true',help='Use only recorded model outputs; fail if any required call is missing')
    args=p.parse_args();config=initialize()
    if args.stage in ['all','sources','generation']:
        from .automated_runtime import MachineClient
        from .automated_sources import run_sources
        client=MachineClient(config,offline=args.offline);cohort,_=run_sources(config,client)
        if args.stage=='sources':return
        from .automated_generation import run_generation
        _,summary=run_generation(cohort,config,client)
        if args.stage=='generation':return
    if args.stage in ['all','diagnostics']:
        # The current actual experiment failed complete-case construction. This
        # separate sensitivity branch never promotes partial rows to primary data.
        from .automated_available_pairs import freeze_available,evaluate_available
        freeze_available(config);evaluate_available()
        if args.stage=='diagnostics':return
    if args.stage in ['all','reports']:
        from .automated_available_pairs import evaluate_available
        evaluate_available()
        if not (AUTO_RESULTS/'results_summary.json').exists():
            from .automated_results import main as reports
            reports()
    if args.stage in ['all','reports','verify']:
        from .automated_verify import verify
        verify()


if __name__=='__main__':main()
