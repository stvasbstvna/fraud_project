# Benchmark v2.1 Execution Runbook

## 1. Inspect technical readiness

```powershell
.\.venv\Scripts\python.exe .\scripts\check_benchmark_v2_1_freeze_readiness.py
```

## 2. Dry-run generation

```powershell
.\.venv\Scripts\python.exe .\scripts\run_benchmark_v2_1_generation.py .\data\benchmark_v2_1\pilot\generation_jobs.csv .\data\benchmark_v2_1\pilot\generated.csv --dry-run
```

## 3. After explicit human authorization, run pilot generation

Set the environment gate only after the research protocol has been reviewed:

```powershell
$env:BENCHMARK_V2_GENERATION_AUTHORIZED="YES"
.\.venv\Scripts\python.exe .\scripts\run_benchmark_v2_1_generation.py .\data\benchmark_v2_1\pilot\generation_jobs.csv .\data\benchmark_v2_1\pilot\generated.csv
```

Complete two independent human reviews using:

`data/benchmark_v2_1/review/pilot_review_sample_v2_1.xlsx`

Do not expose detector outputs to reviewers.

## 4. Compute linguistic-distance measurements after generation

```powershell
.\.venv\Scripts\python.exe .\analysis\benchmark_v2_1_distance_metrics.py .\data\benchmark_v2_1\pilot\generated.csv .\results\benchmark_v2_1\pilot\distance_metrics.csv
```

## 5. Build/update freeze manifest

```powershell
.\.venv\Scripts\python.exe .\scripts\build_benchmark_v2_1_freeze_package.py
```

## 6. Run tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## 7. Full generation

Only after pilot review, adjudication, observed attrition decision, and full freeze:

```powershell
$env:BENCHMARK_V2_GENERATION_AUTHORIZED="YES"
.\.venv\Scripts\python.exe .\scripts\run_benchmark_v2_1_generation.py .\data\benchmark_v2_1\full\generation_jobs.csv .\data\benchmark_v2_1\full\generated.csv
```

## 8. Confirmatory evaluation

Run only the existing frozen detector-evaluation pipeline. The detector output must contain:

`model, frame_id, condition, true_label, prediction, phishing_probability, inclusion_status`

Then:

```powershell
.\.venv\Scripts\python.exe .\analysis\benchmark_v2_1_confirmatory_analysis.py .\results\benchmark_v2_1\frozen_detector_predictions.csv .\results\benchmark_v2_1\confirmatory_results.csv
```

Do not tune the models, prompts, thresholds, or exclusion rules after inspecting results.
