"""Preregistered frame-aware Benchmark v2.1 dose-response analysis.

Consumes only frozen detector output already joined to detector-independent distance
metrics. It never trains, predicts, selects, or excludes rows by performance.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.stats import ttest_1samp

ROOT = Path(__file__).resolve().parents[1]
FAMILY_PATH = ROOT / "configs/benchmark_v2_1_confirmatory_family.yaml"
CONDITIONS = [f"C{i}" for i in range(7)]
REQUIRED = {
    "model", "frame_id", "condition", "true_label", "prediction",
    "phishing_probability", "combined_surface_distance", "inclusion_status",
}


def load_family(path: Path = FAMILY_PATH) -> dict:
    family = yaml.safe_load(path.read_text(encoding="utf-8"))
    ids = [item["id"] for item in family["hypotheses"]]
    if len(ids) != 7 or len(ids) != len(set(ids)):
        raise ValueError("v2.1 confirmatory family must contain seven unique dose-response hypotheses")
    return family


def holm_adjust(pvalues: list[float]) -> list[float]:
    values = np.asarray(pvalues, dtype=float); order = np.argsort(values)
    adjusted = np.empty(len(values)); running = 0.0
    for rank, index in enumerate(order):
        running = max(running, (len(values) - rank) * values[index])
        adjusted[index] = min(1.0, running)
    return adjusted.tolist()


def _logit(values: pd.Series) -> pd.Series:
    p = values.astype(float).clip(1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def _slope(group: pd.DataFrame, endpoint: str) -> float:
    x = group["combined_surface_distance"].astype(float).to_numpy()
    y = group[endpoint].astype(float).to_numpy()
    if len(x) != 7 or np.ptp(x) <= 0:
        return np.nan
    return float(np.polyfit(x, y, 1)[0])


def _one_sample(values: pd.Series) -> tuple[int, float, float]:
    clean = values.dropna().astype(float)
    if len(clean) < 2:
        return len(clean), float(clean.mean()) if len(clean) else np.nan, 1.0
    test = ttest_1samp(clean, 0.0, alternative="two-sided")
    return len(clean), float(clean.mean()), float(test.pvalue)


def analyze(frame: pd.DataFrame, family: dict | None = None) -> pd.DataFrame:
    family = family or load_family()
    missing = REQUIRED - set(frame.columns)
    if missing: raise ValueError(f"missing columns: {sorted(missing)}")
    if not frame["inclusion_status"].eq("final_included").all():
        raise ValueError("confirmatory input must contain only final_included rows")
    data = frame[frame["true_label"].eq("phishing_scam")].copy()
    expected = len(CONDITIONS) * data["model"].nunique()
    counts = data.groupby("frame_id").size()
    if counts.empty or not counts.eq(expected).all():
        raise ValueError("every phishing frame must contain C0-C6 for both frozen detectors")
    if data.duplicated(["model", "frame_id", "condition"]).any():
        raise ValueError("duplicate model/frame/condition rows")
    data["logit_probability"] = _logit(data["phishing_probability"])
    phishing_value = data["prediction"].astype(str).isin({"phishing_scam", "1", "True", "true"})
    data["false_negative"] = (~phishing_value).astype(int)

    slopes = []
    for (frame_id, model), group in data.groupby(["frame_id", "model"]):
        slopes.append({"frame_id": frame_id, "model": model,
                       "continuous_slope": _slope(group, "logit_probability"),
                       "binary_slope": _slope(group, "false_negative")})
    slopes = pd.DataFrame(slopes)
    cont = slopes.pivot(index="frame_id", columns="model", values="continuous_slope")
    binary = slopes.pivot(index="frame_id", columns="model", values="binary_slope")
    models = sorted(cont.columns)
    if len(models) != 2: raise ValueError("exactly two frozen detector models are required")

    rows = []
    def add(hid: str, values: pd.Series) -> None:
        n, effect, p = _one_sample(values)
        spec = next(item for item in family["hypotheses"] if item["id"] == hid)
        rows.append({"hypothesis_id": hid, "tier": spec["tier"], "n_frames": n,
                     "effect_estimate": effect, "raw_p": p})

    add("H1_CONTINUOUS_DISTANCE_TREND", cont.mean(axis=1))
    add("H2_BINARY_FN_DISTANCE_TREND", binary.mean(axis=1))

    contrast_ids = [item for item in family["hypotheses"] if "conditions" in item]
    wide = data.pivot(index="frame_id", columns=["model", "condition"], values="logit_probability")
    for spec in contrast_ids:
        before, after = spec["conditions"]
        differences = pd.concat([wide[(model, after)] - wide[(model, before)] for model in models], axis=1).mean(axis=1)
        add(spec["id"], differences)

    if [row["hypothesis_id"] for row in rows] != [item["id"] for item in family["hypotheses"]]:
        raise RuntimeError("analysis hypotheses do not match preregistered order")
    adjusted = holm_adjust([row["raw_p"] for row in rows])
    alpha = float(family["familywise_alpha"])
    for row, value in zip(rows, adjusted):
        row["holm_adjusted_p"] = value; row["reject_holm_0_05"] = bool(value <= alpha)
        row["family_version"] = family["family_version"]
    for hid, values in (
        ("H3_CONTINUOUS_DETECTOR_DISTANCE_INTERACTION", cont[models[0]] - cont[models[1]]),
        ("H4_BINARY_DETECTOR_DISTANCE_INTERACTION", binary[models[0]] - binary[models[1]]),
    ):
        n, effect, p = _one_sample(values)
        rows.append({"hypothesis_id": hid, "tier": "EXPLORATORY", "n_frames": n,
                     "effect_estimate": effect, "raw_p": p, "holm_adjusted_p": np.nan,
                     "reject_holm_0_05": False, "family_version": family["family_version"]})
    return pd.DataFrame(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path); parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    result = analyze(pd.read_csv(args.input), load_family())
    args.output.parent.mkdir(parents=True, exist_ok=True); result.to_csv(args.output, index=False)
    metadata = {"confirmatory": True, "family": load_family()["family_version"],
                "hypotheses": result.loc[~result.tier.eq("EXPLORATORY"), "hypothesis_id"].tolist(),
                "exploratory": result.loc[result.tier.eq("EXPLORATORY"), "hypothesis_id"].tolist()}
    args.output.with_suffix(".json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(result.to_string(index=False)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
