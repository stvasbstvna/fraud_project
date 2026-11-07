# Project status for HORIZONS

Generated from the current local CSV/JSON artifacts; no detector or API was run by this builder.

## Frozen Benchmark v1 rewrite experiment

- Frozen banking test: **156** messages (146 phishing, 10 legitimate).
- Generation: **153 completed**, **3 rejected by safety checks**.
- Human semantic review: **153 approved**, **0 rejected**, **0 pending** among rewrite rows.
- Current paired evaluation: **153 pairs**, including **143 phishing pairs**; **human-approved paired evaluation**.

## Recorded paired results

- **TF-IDF logistic regression**: recall 98.6% → 97.9%; F1 96.9% → 96.2%; detected→missed `1`; mean confidence drop `-0.0004` (95% bootstrap CI `[-0.0063, 0.0056]`); exact McNemar `p=1.0000`.
- **TF-IDF random forest**: recall 97.9% → 97.2%; F1 95.6% → 95.2%; detected→missed `1`; mean confidence drop `-0.0003` (95% bootstrap CI `[-0.0065, 0.0057]`); exact McNemar `p=1.0000`.

Both models show one additional phishing miss after rewriting. Neither exact McNemar test is significant, and both confidence-drop intervals include zero. The recorded negative mean “confidence drop” means average phishing probability increased slightly after rewriting, not decreased.

## General-performance context

The frozen baseline validation and banking-test metrics remain separate from rewrite robustness. On the ten legitimate paired controls, specificity is low (logistic regression 30%→20%; random forest 0%→0%), indicating a false-positive/generalization limitation distinct from phishing recall.

## Limitations and permitted claims

- All 153 evaluated rewrite pairs have recorded human approval.
- Only 10 legitimate controls are present, so specificity estimates are unstable.
- A one-case transition per model and `p=1.0` do not establish classification degradation.
- Confidence changes and threshold-crossing failures are different outcomes; the current confidence intervals include zero.
- Benchmark v2 pilot records are researcher-authored workflow-calibration material, never detector evidence.
- No result should be selected or rewritten using detector feedback.
