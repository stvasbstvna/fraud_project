"""Flag banking candidates for human review; do not treat flags as final labels."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

BANK_TERMS = {
    "institution": ["bank", "credit union", "card issuer"],
    "account": ["bank account", "checking account", "savings account", "account access", "online banking"],
    "card": ["debit card", "credit card", "card ending", "card transaction", "atm"],
    "transfer": ["wire transfer", "bank transfer", "direct deposit", "payment reversed", "transfer pending"],
    "security": ["fraud alert", "unusual transaction", "verify your account", "banking password", "security code"],
}


def find_banking_terms(text: object) -> list[str]:
    value = str(text).lower()
    matches = []
    for family, terms in BANK_TERMS.items():
        if any(re.search(rf"\b{re.escape(term)}\b", value) for term in terms):
            matches.append(family)
    return matches


def flag_candidates(frame: pd.DataFrame, text_column: str = "text") -> pd.DataFrame:
    if text_column not in frame:
        raise ValueError(f"Missing text column: {text_column}")
    result = frame.copy()
    result["banking_matches"] = result[text_column].map(lambda x: "|".join(find_banking_terms(x)))
    result["banking_candidate"] = result["banking_matches"].ne("")
    result["banking_label"] = "unreviewed"
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--text-column", default="text")
    args = parser.parse_args()
    output = flag_candidates(pd.read_csv(args.input), args.text_column)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False)


if __name__ == "__main__":
    main()
