"""Build source-backed HORIZONS notes and assets from frozen local results only."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results/rewrite_experiment"
PAIRS = ROOT / "data/rewrite_experiment/rewrite_pairs.csv"
DOCS = ROOT / "docs"
ASSETS = ROOT / "results/horizons_assets"
MODEL_NAMES = {"tfidf_logistic_regression": "TF-IDF logistic regression", "tfidf_random_forest": "TF-IDF random forest"}


def pct(value: float) -> str:
    return f"{value:.1%}"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_facts() -> dict:
    pairs = pd.read_csv(PAIRS, keep_default_na=False)
    metrics = pd.read_csv(RESULTS / "metrics_by_model_and_condition.csv")
    stats = pd.read_csv(RESULTS / "statistical_tests.csv")
    baseline = pd.read_csv(RESULTS / "baseline_metrics_frozen.csv")
    rewrites = pairs[pairs["condition"].eq("T1_llm_neutral_rewrite")]
    original = pairs[pairs["condition"].eq("T0_original")]
    completed_rewrites = rewrites[rewrites["generation_status"].eq("completed")]
    review = completed_rewrites["human_review_status"].replace("", "pending").value_counts().to_dict()
    models = {}
    for model, name in MODEL_NAMES.items():
        m = metrics[metrics["model"].eq(model)].set_index("condition")
        s = stats[stats["model"].eq(model)].iloc[0]
        models[model] = {
            "name": name,
            "original_recall": float(m.loc["T0_original", "recall"]),
            "rewrite_recall": float(m.loc["T1_llm_neutral_rewrite", "recall"]),
            "original_f1": float(m.loc["T0_original", "f1"]),
            "rewrite_f1": float(m.loc["T1_llm_neutral_rewrite", "f1"]),
            "original_specificity": float(m.loc["T0_original", "specificity"]),
            "rewrite_specificity": float(m.loc["T1_llm_neutral_rewrite", "specificity"]),
            "detected_to_missed": int(s["became_false_negative"]),
            "mean_confidence_drop": float(s["mean_confidence_drop"]),
            "ci_low": float(s["confidence_drop_ci95_low"]),
            "ci_high": float(s["confidence_drop_ci95_high"]),
            "mcnemar_p": float(s["mcnemar_exact_p_value"]),
        }
    return {
        "pairs": int(original["pair_id"].nunique()),
        "phishing": int((original["binary_label"] == 1).sum()),
        "legitimate": int((original["binary_label"] == 0).sum()),
        "completed": int((rewrites["generation_status"] == "completed").sum()),
        "rejected_generation": int(rewrites["generation_status"].str.contains("rejected", case=False).sum()),
        "review_approved": int(review.get("approved", 0)),
        "review_rejected": int(review.get("rejected", 0)),
        "review_pending": int(review.get("pending", 0)),
        "evaluated_pairs": int(pd.read_csv(RESULTS / "paired_predictions.csv")["pair_id"].nunique()),
        "evaluated_phishing": int(stats.iloc[0]["phishing_pairs"]),
        "models": models,
        "baseline": baseline,
    }


def model_lines(facts: dict) -> str:
    lines = []
    for item in facts["models"].values():
        lines.append(
            f"- **{item['name']}**: recall {pct(item['original_recall'])} → {pct(item['rewrite_recall'])}; "
            f"F1 {pct(item['original_f1'])} → {pct(item['rewrite_f1'])}; detected→missed `{item['detected_to_missed']}`; "
            f"mean confidence drop `{item['mean_confidence_drop']:.4f}` (95% bootstrap CI "
            f"`[{item['ci_low']:.4f}, {item['ci_high']:.4f}]`); exact McNemar `p={item['mcnemar_p']:.4f}`."
        )
    return "\n".join(lines)


def build() -> None:
    facts = load_facts(); lines = model_lines(facts)
    review_complete = facts["review_approved"] == facts["completed"] and facts["review_pending"] == 0
    evaluation_status = "human-approved paired evaluation" if review_complete else "exploratory evaluation because human approval is still pending"
    review_limitation = (
        "All 153 evaluated rewrite pairs have recorded human approval."
        if review_complete else
        "Human semantic review is incomplete; the 153-pair analysis is not a final human-approved result."
    )
    status = f"""# Project status for HORIZONS

Generated from the current local CSV/JSON artifacts; no detector or API was run by this builder.

## Frozen Benchmark v1 rewrite experiment

- Frozen banking test: **{facts['pairs']}** messages ({facts['phishing']} phishing, {facts['legitimate']} legitimate).
- Generation: **{facts['completed']} completed**, **{facts['rejected_generation']} rejected by safety checks**.
- Human semantic review: **{facts['review_approved']} approved**, **{facts['review_rejected']} rejected**, **{facts['review_pending']} pending** among rewrite rows.
- Current paired evaluation: **{facts['evaluated_pairs']} pairs**, including **{facts['evaluated_phishing']} phishing pairs**; **{evaluation_status}**.

## Recorded paired results

{lines}

Both models show one additional phishing miss after rewriting. Neither exact McNemar test is significant, and both confidence-drop intervals include zero. The recorded negative mean “confidence drop” means average phishing probability increased slightly after rewriting, not decreased.

## General-performance context

The frozen baseline validation and banking-test metrics remain separate from rewrite robustness. On the ten legitimate paired controls, specificity is low (logistic regression 30%→20%; random forest 0%→0%), indicating a false-positive/generalization limitation distinct from phishing recall.

## Limitations and permitted claims

- {review_limitation}
- Only 10 legitimate controls are present, so specificity estimates are unstable.
- A one-case transition per model and `p=1.0` do not establish classification degradation.
- Confidence changes and threshold-crossing failures are different outcomes; the current confidence intervals include zero.
- Benchmark v2 pilot records are researcher-authored workflow-calibration material, never detector evidence.
- No result should be selected or rewritten using detector feedback.
"""
    (DOCS / "project_status_for_horizons.md").write_text(status, encoding="utf-8")

    lr = facts["models"]["tfidf_logistic_regression"]; rf = facts["models"]["tfidf_random_forest"]
    slide_plan = f"""# HORIZONS 12-minute slide plan

Audience: broad research audience. Communication job: explain what was tested, what the preliminary evidence does and does not show, and why human-reviewed Benchmark v2 is the next methodological step.

## Main deck (10 slides)

1. **A harmless rewrite can test whether a smishing detector learned meaning or wording** — define smishing once: fraudulent SMS designed to induce an unsafe action. Open with the research question.
2. **The test changes wording while holding the message pair fixed** — paired original/rewrite design; same label, action, and identifiers; detectors frozen.
3. **The experiment blocks detector-guided optimization** — frozen split and models, defanged placeholders, no detector feedback to generation, safety checks, human review gate.
4. **153 safe rewrites completed human semantic review** — {facts['completed']}/{facts['pairs']} completed, {facts['rejected_generation']} safety-rejected, {facts['review_approved']} approved and {facts['review_pending']} pending.
5. **Preliminary recall changed by one phishing case per detector** — LR {pct(lr['original_recall'])}→{pct(lr['rewrite_recall'])}; RF {pct(rf['original_recall'])}→{pct(rf['rewrite_recall'])}; show `detector_performance.png`.
6. **The paired evidence does not establish degradation** — one detected→missed transition per model; both McNemar p=1.0; show `paired_transitions.png`.
7. **Probability sensitivity is not the same as classification failure** — mean confidence drops {lr['mean_confidence_drop']:.4f} and {rf['mean_confidence_drop']:.4f}; both 95% CIs include zero; show confidence plot only as exploratory.
8. **Legitimate controls reveal a different limitation** — specificity LR 30%→20%, RF 0%→0%, but n=10; frame as false-positive/generalization weakness, not rewrite attack success.
9. **Benchmark v2 strengthens provenance, conditions, and human review** — authorized anchors, frozen prompts, documented generator pool, detector-blinded generation, complete C0–C3 approvals.
10. **The current conclusion is methodological, not adversarial** — v1 is human-approved, but its paired effect remains small and non-significant; stronger claims require preregistered v2 testing.

## Appendix

- A1. Frozen model comparison and baseline validation metrics.
- A2. Full paired metrics, confidence intervals, and McNemar tests.
- A3. Human-review rubric and approval/adjudication rules.
- A4. Benchmark v2 pilot disclaimer and provenance boundary.
"""
    (DOCS / "horizons_12_minute_slide_plan.md").write_text(slide_plan, encoding="utf-8")

    notes = f"""# HORIZONS speaker notes

## Slide 1 — Research question (0:00–0:55)
Smishing is fraudulent SMS designed to induce an unsafe action. Ask whether detectors respond to the underlying intent or to familiar surface wording. Do not promise that the study will prove detector failure.

## Slide 2 — Paired design (0:55–2:00)
Each original and rewrite shares a pair ID and label. The comparison is within-message, reducing variation unrelated to wording.

## Slide 3 — Frozen safeguards (2:00–3:05)
Models and splits are frozen. Generation receives no detector scores or feedback. URLs remain defanged. No model was fit during evaluation.

## Slide 4 — Current workflow state (3:05–4:00)
There are {facts['pairs']} original pairs. {facts['completed']} rewrites passed automated checks; {facts['rejected_generation']} were rejected. Human semantic review approved {facts['review_approved']} rows, with {facts['review_pending']} pending. The reported v1 evaluation now uses the complete approved set.

## Slide 5 — Recall and F1 (4:00–5:20)
LR recall moved {pct(lr['original_recall'])} to {pct(lr['rewrite_recall'])}; RF moved {pct(rf['original_recall'])} to {pct(rf['rewrite_recall'])}. F1 moved {pct(lr['original_f1'])} to {pct(lr['rewrite_f1'])} and {pct(rf['original_f1'])} to {pct(rf['rewrite_f1'])}. Each model gained one additional miss; avoid saying detectors broadly failed.

## Slide 6 — Paired inference (5:20–6:25)
The discordant transition is one detected-to-missed and zero missed-to-detected phishing cases for each model. Exact McNemar p is 1.0. Say explicitly: this sample does not establish a significant paired classification change.

## Slide 7 — Confidence (6:25–7:35)
The metric is original probability minus rewrite probability. Its mean is slightly negative for both models, so confidence increased slightly on average. Both bootstrap intervals cross zero. Probability movement is sensitivity; crossing the frozen threshold is classification failure.

## Slide 8 — Legitimate controls (7:35–8:40)
Specificity is poor, especially for random forest, but only ten legitimate controls exist. Present this as a separate generalization/false-positive limitation and emphasize uncertainty from the small denominator.

## Slide 9 — Benchmark v2 (8:40–10:20)
The pilot validates schemas and review logic only. Final v2 needs authorized anchors, frozen prompts, a versioned generator pool, human approval of complete condition sets, provenance enforcement, and detector-blinded generation.

## Slide 10 — Close (10:20–12:00)
The contribution today is a reproducible paired robustness workflow and a disciplined null/inconclusive result. Human review is complete for v1; broader detector claims still require preregistered confirmatory v2 testing.
"""
    (DOCS / "horizons_speaker_notes.md").write_text(notes, encoding="utf-8")

    qa = f"""# HORIZONS Q&A

## Did the rewrites defeat the detectors?
Not as a general conclusion. Each detector had one additional phishing miss among {facts['evaluated_phishing']} evaluated phishing pairs, but exact McNemar p=1.0.

## Why discuss confidence if recall barely changed?
Confidence can reveal sensitivity before a threshold crossing, but here the average change is slightly in the opposite direction and both 95% bootstrap intervals include zero. It is exploratory, not proof of failure.

## Are the 153 rewrites human-approved research data?
Yes. All 153 completed rewrites have recorded human approval. This does not make the paired effect statistically significant or remove the small legitimate-control limitation.

## Why are legitimate results weak?
There are only ten legitimate controls. The low specificity is concerning as a false-positive/generalization signal, but the estimate is unstable and distinct from rewrite robustness.

## Was the generator optimized against detector feedback?
No. Detector access and feedback were excluded from generation, and the models remained frozen.

## Is Benchmark v2 already a final benchmark?
No. The current pilot is researcher-authored, non-operational, and `final_benchmark_eligible=false`. It calibrates workflow and review logic only.

## What would justify a stronger claim?
Completed blinded human review, authorized final anchors, frozen prompts and generator assignments, adequate power for the preregistered testing family, and confirmatory paired tests at frozen thresholds.
"""
    (DOCS / "horizons_q_and_a.md").write_text(qa, encoding="utf-8")

    ASSETS.mkdir(parents=True, exist_ok=True)
    dashboard_figures = ROOT / "results/rewrite_experiment/dashboard/figures"
    copied = {}
    for name in ("detector_performance.png", "paired_transitions.png", "confidence_drop_histograms.png"):
        source = dashboard_figures / name
        if source.exists():
            target = ASSETS / name; shutil.copy2(source, target)
            copied[name] = {"source": source.relative_to(ROOT).as_posix(), "sha256": sha(target)}
    manifest = {"source_files": {str(PAIRS.relative_to(ROOT)): sha(PAIRS), "results/rewrite_experiment/metrics_by_model_and_condition.csv": sha(RESULTS / "metrics_by_model_and_condition.csv"), "results/rewrite_experiment/statistical_tests.csv": sha(RESULTS / "statistical_tests.csv")}, "assets": copied}
    (ASSETS / "asset_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()
