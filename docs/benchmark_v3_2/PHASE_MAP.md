# Phase map

| Phase | Research question | Input dataset | Models | Prompts | Outputs | Current status | Relationship to prior versions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | Original detection | Preserved v3 final_run | LR/RF/ModernBERT | Historical only | Existing final_run experimentA | Completed historical exploratory | Read-only reference, no rerun or pooling |
| B | Source generalization | Preserved Gateway167phishing-only test | Separate v3 source-fitted LR/RF/ModernBERT | Historical only | Existing final_run experimentB | Completed historical; temporal not run | Not universal model ranking |
| C | Intent/action-preserving linguistic robustness | Newv3.2 source and rewrite freezes | Reused read-only v3 primary models | External v1 source3/generation4/rewrite3 | Newv3.2 predictions/statistics/figures | PRIMARY_FAILED_COMPLETENESS_EXPLORATORY_AVAILABLE_PAIRS_COMPLETED | New protocol/run; old39pairs unchanged and not merged |
