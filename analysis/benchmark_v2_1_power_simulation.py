"""Prospective repeated-frame power sensitivity for the seven-test v2.1 Holm family."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import yaml
from scipy.special import expit, logit
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
FAMILY_PATH = ROOT / "configs/benchmark_v2_1_confirmatory_family.yaml"
DISTANCE = np.array([0.0, 0.15, 0.30, 0.30, 0.50, 0.75, 1.0])
PROFILES = {
    "small": {"score_slope": -0.08, "fn_increase_at_max": 0.02, "contrast_logit": -0.05, "detector_interaction": 0.03},
    "target": {"score_slope": -0.15, "fn_increase_at_max": 0.04, "contrast_logit": -0.10, "detector_interaction": 0.06},
    "large": {"score_slope": -0.25, "fn_increase_at_max": 0.06, "contrast_logit": -0.15, "detector_interaction": 0.10},
}


def hypothesis_ids() -> list[str]:
    family = yaml.safe_load(FAMILY_PATH.read_text(encoding="utf-8"))
    return [item["id"] for item in family["hypotheses"]]


def holm_rejections(pvalues: np.ndarray, alpha: float = 0.05) -> np.ndarray:
    order = np.argsort(pvalues); rejected = np.zeros(len(pvalues), dtype=bool)
    for rank, index in enumerate(order):
        if pvalues[index] <= alpha / (len(pvalues) - rank): rejected[index] = True
        else: break
    return rejected


def _pvalues(values: np.ndarray) -> np.ndarray:
    """Two-sided one-sample t p-values for simulation x frame values."""
    n = values.shape[1]; mean = values.mean(axis=1); sd = values.std(axis=1, ddof=1)
    statistic = np.divide(mean, sd / np.sqrt(n), out=np.zeros_like(mean), where=sd > 0)
    return 2 * student_t.sf(np.abs(statistic), df=n - 1)


def _slopes(values: np.ndarray) -> np.ndarray:
    centered = DISTANCE - DISTANCE.mean(); denominator = np.sum(centered**2)
    return np.sum(values * centered, axis=-1) / denominator


def simulate(n: int, profile: dict[str, float], simulations: int, seed: int, batch_size: int = 100) -> dict:
    rng = np.random.default_rng(seed); ids = hypothesis_ids()
    rejects = np.zeros(len(ids), dtype=int)
    base_fn = 0.05
    fn_beta = logit(base_fn + profile["fn_increase_at_max"]) - logit(base_fn)
    completed = 0
    while completed < simulations:
        batch = min(batch_size, simulations - completed)
        frame_effect = rng.normal(0, 0.55, size=(batch, n, 1, 1))
        common_noise = rng.normal(0, 0.30, size=(batch, n, 1, 7))
        model_noise = rng.normal(0, 0.35, size=(batch, n, 2, 7))
        signs = np.array([-0.5, 0.5]).reshape(1, 1, 2, 1)
        offsets = np.array([0, .5, .8, 1.8, 1.0, 1.5, 2.0]) * profile["contrast_logit"]
        continuous = (frame_effect + common_noise + model_noise
                      + profile["score_slope"] * DISTANCE.reshape(1,1,1,7)
                      + signs * profile["detector_interaction"] * DISTANCE.reshape(1,1,1,7)
                      + offsets.reshape(1,1,1,7))
        fn_frame = rng.normal(0, 0.65, size=(batch, n, 1, 1))
        fn_logit = (logit(base_fn) + fn_frame + fn_beta * DISTANCE.reshape(1,1,1,7)
                    + signs * profile["detector_interaction"] * DISTANCE.reshape(1,1,1,7))
        binary = rng.random(size=(batch,n,2,7)) < expit(fn_logit)
        continuous_slopes = _slopes(continuous); binary_slopes = _slopes(binary.astype(float))
        series = [continuous_slopes.mean(axis=2), binary_slopes.mean(axis=2)]
        for before, after in ((0,1),(2,3),(0,4),(0,5),(0,6)):
            series.append((continuous[:,:,:,after]-continuous[:,:,:,before]).mean(axis=2))
        p_matrix = np.column_stack([_pvalues(values) for values in series])
        for row in p_matrix: rejects += holm_rejections(row)
        completed += batch
    powers = rejects / simulations
    return {"n_phishing_frames": n, "simulations": simulations, "seed": seed,
            "hypothesis_power": dict(zip(ids, powers.tolist())),
            "minimum_primary_power": float(powers[:2].min()),
            "minimum_all_confirmatory_power": float(powers.min())}


def build_outputs(output_dir: Path, simulations: int = 1000, seed: int = 20260828) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True); rows=[]; scenarios=[]
    for pi,(name,profile) in enumerate(PROFILES.items()):
        for ni,n in enumerate((500,750,1000)):
            result=simulate(n,profile,simulations,seed+pi*10+ni); scenarios.append({"profile":name,"assumptions":profile,**result})
            for hid,power in result["hypothesis_power"].items():
                rows.append({"analysis_role":"prospective_sensitivity_not_detector_informed","profile":name,"n_phishing_frames":n,**profile,"hypothesis_id":hid,"holm_rejection_power":power,"simulations":simulations,"seed":result["seed"]})
    with (output_dir/"power_simulation.csv").open("w",encoding="utf-8",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    summary={"status":"v2.1_prospective_sensitivity_complete_human_pilot_gates_pending","family_version":"bv21-dose-response-primary-v1","hypothesis_ids":hypothesis_ids(),"hypothesis_count":7,"familywise_alpha":0.05,"holm":True,"within_frame_conditions":7,"detectors":2,"target_power_options":[0.80,0.90],"baseline_false_negative_rate_assumption":0.05,"scenarios":scenarios}
    (output_dir/"power_summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    lines=["# Benchmark v2.1 dose-response power sensitivity","","This prospective simulation uses seven repeated conditions and two correlated detector outcomes per frame, then applies Holm jointly to the seven new dose-response confirmatory hypotheses. Assumptions are not derived from v2.1 detector results.","","| Profile | N | Minimum primary power | Minimum all-confirmatory power |","|---|---:|---:|---:|"]
    for s in scenarios: lines.append(f"| {s['profile']} | {s['n_phishing_frames']} | {s['minimum_primary_power']:.3f} | {s['minimum_all_confirmatory_power']:.3f} |")
    (output_dir/"power_summary.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    return summary


def main(argv: list[str] | None=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--output-dir",type=Path,default=ROOT/"results/benchmark_v2_1/power"); parser.add_argument("--simulations",type=int,default=1000); parser.add_argument("--seed",type=int,default=20260828); args=parser.parse_args(argv)
    summary=build_outputs(args.output_dir,args.simulations,args.seed); print(json.dumps({"status":summary["status"],"scenarios":len(summary["scenarios"]),"hypotheses":7})); return 0

if __name__=="__main__": raise SystemExit(main())
