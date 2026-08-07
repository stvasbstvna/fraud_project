import pandas as pd
from pathlib import Path

PROCESSED_DIR = Path("data/processed")
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

files = [
    "unified_text_messages.csv",
    "banking_candidates.csv",
    "banking_manual_review.csv",
    "banking_human_written.csv",
    "banking_ai_generated.csv",
    "banking_ai_rewritten.csv",
]

summary_rows = []

for file_name in files:
    path = PROCESSED_DIR / file_name

    if not path.exists():
        summary_rows.append({
            "file": file_name,
            "exists": "no",
            "rows": 0,
            "columns": ""
        })
        print(f"Missing: {path}")
        continue

    df = pd.read_csv(path)

    summary_rows.append({
        "file": file_name,
        "exists": "yes",
        "rows": len(df),
        "columns": ", ".join(df.columns)
    })

    print("\n" + "=" * 80)
    print(file_name)
    print("=" * 80)
    print("Rows:", len(df))
    print("Columns:", list(df.columns))

    if "label" in df.columns:
        print("\nLabel distribution:")
        print(df["label"].value_counts(dropna=False))

    if "source_dataset" in df.columns:
        print("\nSource distribution:")
        print(df["source_dataset"].value_counts(dropna=False).head(20))

    if "is_human_written" in df.columns:
        print("\nHuman-written distribution:")
        print(df["is_human_written"].value_counts(dropna=False))

    if "is_ai_generated" in df.columns:
        print("\nAI-generated distribution:")
        print(df["is_ai_generated"].value_counts(dropna=False))

summary = pd.DataFrame(summary_rows)
summary.to_csv(RESULTS_DIR / "dataset_file_summary.csv", index=False)

print("\nSaved summary to results/dataset_file_summary.csv")