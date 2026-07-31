"""Transparent intent/action features for mitigation experiments."""

from __future__ import annotations

import re
import pandas as pd

PATTERNS = {
    "action_click": r"\b(?:click|tap|visit|follow).{0,25}\b(?:link|url|website)\b",
    "action_call": r"\b(?:call|phone|dial).{0,25}\b(?:number|support|us)\b",
    "action_reply": r"\b(?:reply|respond|email us)\b",
    "action_disclose": r"\b(?:verify|confirm|provide|enter).{0,35}\b(?:password|pin|code|credential|account)\b",
    "action_transfer": r"\b(?:transfer|send|pay|approve).{0,25}\b(?:money|funds|payment|transaction)\b",
    "time_pressure": r"\b(?:immediately|urgent|now|today|within \d+ (?:minutes|hours)|suspend|locked)\b",
    "url_present": r"(?i)\b(?:https?://|www\.|\[URL\])",
}


def extract_action_features(texts: pd.Series) -> pd.DataFrame:
    clean = texts.fillna("").astype(str)
    output = pd.DataFrame(index=texts.index)
    for name, pattern in PATTERNS.items():
        output[name] = clean.str.contains(pattern, flags=re.IGNORECASE, regex=True).astype(int)
    output["character_count"] = clean.str.len()
    output["token_count"] = clean.str.split().str.len()
    return output
