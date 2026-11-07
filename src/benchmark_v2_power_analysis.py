"""Assumption-driven approximate power planning for Benchmark v2."""

from __future__ import annotations

import argparse
import json
import math
from statistics import NormalDist


def validate_assumptions(
    baseline_recall: float,
    expected_recall_difference: float,
    discordant_pair_rate: float,
    alpha: float,
    power: float,
    phishing_count: int,
    legitimate_count: int,
    variants_per_scenario: int,
    prompt_pilot_count: int = 0,
    quality_validation_count: int = 0,
) -> None:
    for name, value in {
        "baseline_recall": baseline_recall,
        "discordant_pair_rate": discordant_pair_rate,
        "alpha": alpha,
        "power": power,
    }.items():
        if not 0 < value < 1:
            raise ValueError(f"{name} must be between 0 and 1")
    if not -1 < expected_recall_difference < 1 or expected_recall_difference == 0:
        raise ValueError("expected_recall_difference must be non-zero and between -1 and 1")
    if discordant_pair_rate < abs(expected_recall_difference):
        raise ValueError("discordant_pair_rate must be at least abs(expected_recall_difference)")
    if not 0 <= baseline_recall - expected_recall_difference <= 1:
        raise ValueError("baseline recall and expected difference imply an invalid comparison recall")
    if phishing_count <= 0 or legitimate_count <= 0 or variants_per_scenario <= 0:
        raise ValueError("scenario counts and variants_per_scenario must be positive integers")
    if prompt_pilot_count < 0 or quality_validation_count < 0:
        raise ValueError("pilot and quality-validation counts cannot be negative")


def approximate_mcnemar_scenarios(difference: float, discordant_rate: float, alpha: float, power: float) -> int:
    """Normal-approximation planning value; exact simulation is required before freeze."""
    delta = abs(difference)
    z_alpha = NormalDist().inv_cdf(1 - alpha / 2)
    z_power = NormalDist().inv_cdf(power)
    variance_alt = max(discordant_rate - delta * delta, 1e-12)
    n = ((z_alpha * math.sqrt(discordant_rate) + z_power * math.sqrt(variance_alt)) / delta) ** 2
    return math.ceil(n)


def wilson_half_width(count: int, proportion: float, alpha: float) -> float:
    z = NormalDist().inv_cdf(1 - alpha / 2)
    denominator = 1 + z * z / count
    return z * math.sqrt(proportion * (1 - proportion) / count + z * z / (4 * count * count)) / denominator


def build_report(args: argparse.Namespace) -> dict[str, object]:
    validate_assumptions(
        args.baseline_recall, args.expected_recall_difference,
        args.discordant_pair_rate, args.alpha, args.power,
        args.phishing_count, args.legitimate_count, args.variants_per_scenario,
        args.prompt_pilot_count, args.quality_validation_count,
    )
    required = approximate_mcnemar_scenarios(
        args.expected_recall_difference, args.discordant_pair_rate, args.alpha, args.power
    )
    comparison_recall = args.baseline_recall - args.expected_recall_difference
    return {
        "status": "approximate_assumption_driven_plan_not_final_sample_size",
        "confirmatory_primary_test_count": 7,
        "confirmatory_multiplicity_method": "Holm across H1/H2/H3 x two detectors plus one H4 interaction",
        "assumptions": vars(args),
        "implied_comparison_recall": comparison_recall,
        "approximate_phishing_scenarios_for_mcnemar": required,
        "confirmatory_final_test_phishing_scenarios": args.phishing_count,
        "confirmatory_final_test_legitimate_scenarios": args.legitimate_count,
        "prompt_development_pilot_scenarios_excluded_from_v2": args.prompt_pilot_count,
        "quality_validation_scenarios_excluded_from_confirmatory_analysis": args.quality_validation_count,
        "confirmatory_final_test_variants": (args.phishing_count + args.legitimate_count) * args.variants_per_scenario,
        "recall_interval_half_width_at_planned_n": wilson_half_width(args.phishing_count, args.baseline_recall, args.alpha),
        "specificity_interval_half_width_example_at_0_90": wilson_half_width(args.legitimate_count, 0.90, args.alpha),
        "warning": "Power is based only on unique untouched confirmatory final-test scenarios. The displayed McNemar approximation is unadjusted; final simulation must model the seven-test Holm family, H2 paired indicators, complete-set attrition, and detector dependence."
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--baseline-recall", type=float, default=0.95)
    result.add_argument("--expected-recall-difference", type=float, default=0.04)
    result.add_argument("--discordant-pair-rate", type=float, default=0.10)
    result.add_argument("--alpha", type=float, default=0.05)
    result.add_argument("--power", type=float, default=0.80)
    result.add_argument("--phishing-count", type=int, default=500)
    result.add_argument("--legitimate-count", type=int, default=500)
    result.add_argument("--variants-per-scenario", type=int, default=4)
    result.add_argument("--prompt-pilot-count", type=int, default=0)
    result.add_argument("--quality-validation-count", type=int, default=0)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        report = build_report(args)
    except ValueError as error:
        parser().error(str(error))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
