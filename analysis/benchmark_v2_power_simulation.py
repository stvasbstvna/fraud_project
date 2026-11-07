"""Deterministic sensitivity simulation for Benchmark v2's seven-test Holm family.

The built-in scenarios are explicitly *not* confirmatory assumptions.  Final
sample size selection requires owner-approved effect, discordance, dependence,
attrition, and target-power values.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import binom

ROOT = Path(__file__).resolve().parents[1]
TESTS = (
    "H1_logistic_regression", "H1_random_forest",
    "H2_logistic_regression", "H2_random_forest",
    "H3_logistic_regression", "H3_random_forest",
    "H4_detector_interaction",
)
PROFILES = {
    "conservative": (0.02, 0.10),
    "target_sensitivity": (0.04, 0.10),
    "optimistic": (0.06, 0.12),
}


def holm_rejections(pvalues: np.ndarray, alpha: float = 0.05) -> np.ndarray:
    """Return Holm step-down rejection indicators in original order."""
    values = np.asarray(pvalues, dtype=float)
    order = np.argsort(values)
    rejected = np.zeros(len(values), dtype=bool)
    for rank, index in enumerate(order):
        if values[index] <= alpha / (len(values) - rank):
            rejected[index] = True
        else:
            break
    return rejected


def exact_mcnemar_p(b: int, c: int) -> float:
    """Two-sided exact conditional binomial p-value for discordant cells."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    lower = sum(math.comb(n, i) for i in range(k + 1)) / (2**n)
    return min(1.0, 2 * lower)


def _p_table(n: int) -> list[np.ndarray]:
    tables = []
    for d in range(n + 1):
        b = np.arange(d + 1)
        k = np.minimum(b, d - b)
        tables.append(np.minimum(1.0, 2 * binom.cdf(k, d, 0.5)))
    return tables


def simulate(n: int, effect: float, discordance: float, simulations: int, seed: int, alpha: float = 0.05) -> dict:
    if not (0 < effect <= discordance < 1):
        raise ValueError("require 0 < effect <= discordance < 1")
    if n <= 0 or simulations <= 0:
        raise ValueError("n and simulations must be positive")
    rng = np.random.default_rng(seed)
    table = _p_table(n)
    directional_probability = (discordance + effect) / (2 * discordance)
    rejection_totals = np.zeros(7, dtype=int)
    any_rejection = 0
    all_rejection = 0
    # Independent tests are a transparent sensitivity assumption, not a claim
    # about the unknown dependence of the two frozen detectors.
    for _ in range(simulations):
        discordant = rng.binomial(n, discordance, size=7)
        favorable = np.array([rng.binomial(int(d), directional_probability) for d in discordant])
        pvalues = np.array([table[int(d)][int(b)] for d, b in zip(discordant, favorable)])
        rejected = holm_rejections(pvalues, alpha)
        rejection_totals += rejected
        any_rejection += int(rejected.any())
        all_rejection += int(rejected.all())
    powers = rejection_totals / simulations
    return {
        "n_scenarios": n, "effect": effect, "discordant_pair_rate": discordance,
        "simulations": simulations, "seed": seed, "alpha": alpha,
        "test_power": dict(zip(TESTS, powers.tolist())),
        "minimum_test_power": float(powers.min()),
        "mean_test_power": float(powers.mean()),
        "probability_any_primary_rejection": any_rejection / simulations,
        "probability_all_primary_rejected": all_rejection / simulations,
    }


def build_outputs(output_dir: Path, simulations: int = 3000, seed: int = 20260827,
                  profiles: dict[str, tuple[float, float]] | None = None,
                  sample_sizes: tuple[int, ...] = (500, 750, 1000)) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    scenarios = []
    selected_profiles = profiles or PROFILES
    for p_index, (profile, (effect, discordance)) in enumerate(selected_profiles.items()):
        for n_index, n in enumerate(sample_sizes):
            result = simulate(n, effect, discordance, simulations, seed + p_index * 10 + n_index)
            scenarios.append({"profile": profile, **result})
            for test, power in result["test_power"].items():
                rows.append({
                    "analysis_role": "sensitivity_not_confirmatory", "profile": profile,
                    "n_scenarios": n, "effect": effect, "discordant_pair_rate": discordance,
                    "test": test, "holm_adjusted_rejection_power": power,
                    "simulations": simulations, "seed": result["seed"],
                })
    csv_path = output_dir / "power_simulation.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    summary = {
        "status": "sensitivity_analysis_complete_confirmatory_assumptions_pending",
        "primary_family": list(TESTS), "primary_test_count": 7,
        "multiplicity": "Holm step-down", "familywise_alpha": 0.05,
        "unit": "unique paired scenario", "primary_outcome": "binary phishing prediction at the detector's frozen threshold",
        "simulation_seed_base": seed, "simulations_per_scenario": simulations,
        "dependence_assumption": "independent primary-test statistics for sensitivity only",
        "confirmatory_decisions_required": ["minimum relevant effects by hypothesis", "discordant-pair rates", "cross-detector/test dependence", "complete-set attrition", "target marginal or joint power"],
        "scenarios": scenarios,
    }
    (output_dir / "power_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    md = ["# Benchmark v2 Holm-family power sensitivity analysis", "", "**Not a final sample-size freeze.** The seven-test Holm procedure is implemented exactly, but the profiles are sensitivity values rather than approved confirmatory assumptions.", "", "| Profile | N | Effect | Discordance | Minimum test power |", "|---|---:|---:|---:|---:|"]
    for row in scenarios:
        md.append(f"| {row['profile']} | {row['n_scenarios']} | {row['effect']:.3f} | {row['discordant_pair_rate']:.3f} | {row['minimum_test_power']:.3f} |")
    md += ["", "Exact conditional-binomial McNemar p-values are calculated for each simulated paired comparison and Holm step-down correction is applied jointly across all seven p-values in every replicate."]
    (output_dir / "power_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    try:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 5))
        for profile in selected_profiles:
            selected = [x for x in scenarios if x["profile"] == profile]
            ax.plot([x["n_scenarios"] for x in selected], [x["minimum_test_power"] for x in selected], marker="o", label=profile)
        ax.axhline(0.8, color="black", linestyle="--", linewidth=1, label="0.80 reference")
        ax.set(xlabel="Unique paired scenarios", ylabel="Minimum marginal Holm rejection power", ylim=(0, 1), title="Benchmark v2 sensitivity analysis (not confirmatory assumptions)")
        ax.legend(); fig.tight_layout(); fig.savefig(output_dir / "power_plot.png", dpi=180); plt.close(fig)
    except ImportError:
        pass
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results/benchmark_v2/power")
    parser.add_argument("--simulations", type=int, default=3000)
    parser.add_argument("--seed", type=int, default=20260827)
    parser.add_argument("--effect", type=float, help="Approved/candidate paired effect for a custom run")
    parser.add_argument("--discordance", type=float, help="Approved/candidate discordant-pair rate for a custom run")
    parser.add_argument("--sample-sizes", type=int, nargs="+", default=[500, 750, 1000])
    args = parser.parse_args(argv)
    if (args.effect is None) != (args.discordance is None):
        parser.error("--effect and --discordance must be supplied together")
    profiles = None if args.effect is None else {"approved_candidate_inputs": (args.effect, args.discordance)}
    summary = build_outputs(args.output_dir, args.simulations, args.seed, profiles, tuple(args.sample_sizes))
    print(json.dumps({"status": summary["status"], "scenarios": len(summary["scenarios"]), "primary_tests": 7}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
