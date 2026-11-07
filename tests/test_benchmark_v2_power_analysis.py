from __future__ import annotations

import unittest

from src.benchmark_v2_power_analysis import approximate_mcnemar_scenarios, build_report, main, parser, validate_assumptions


class BenchmarkV2PowerAnalysisTests(unittest.TestCase):
    def test_valid_assumptions_and_positive_scenario_count(self) -> None:
        validate_assumptions(0.95, 0.04, 0.10, 0.05, 0.80, 500, 500, 4)
        self.assertGreater(approximate_mcnemar_scenarios(0.04, 0.10, 0.05, 0.80), 0)

    def test_cli_argument_validation_rejects_impossible_probabilities(self) -> None:
        with self.assertRaises(SystemExit) as context:
            main(["--baseline-recall", "1.5"])
        self.assertEqual(context.exception.code, 2)

    def test_discordance_must_cover_expected_difference(self) -> None:
        with self.assertRaisesRegex(ValueError, "discordant_pair_rate"):
            validate_assumptions(0.95, 0.20, 0.10, 0.05, 0.80, 500, 500, 4)

    def test_more_power_requires_no_fewer_scenarios(self) -> None:
        low = approximate_mcnemar_scenarios(0.04, 0.10, 0.05, 0.80)
        high = approximate_mcnemar_scenarios(0.04, 0.10, 0.05, 0.90)
        self.assertGreaterEqual(high, low)

    def test_only_final_test_counts_receive_confirmatory_credit(self) -> None:
        args = parser().parse_args(["--phishing-count", "400", "--legitimate-count", "450", "--prompt-pilot-count", "80", "--quality-validation-count", "120"])
        report = build_report(args)
        self.assertEqual(report["confirmatory_final_test_phishing_scenarios"], 400)
        self.assertEqual(report["prompt_development_pilot_scenarios_excluded_from_v2"], 80)
        self.assertEqual(report["confirmatory_final_test_variants"], (400 + 450) * 4)
        self.assertEqual(report["confirmatory_primary_test_count"], 7)
        self.assertIn("Holm", report["confirmatory_multiplicity_method"])


if __name__ == "__main__":
    unittest.main()
