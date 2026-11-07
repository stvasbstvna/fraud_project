"""Compute detector-independent linguistic distance measurements for Benchmark v2.1."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")

def tokens(s: str) -> set[str]:
    return set(TOKEN_RE.findall(str(s).lower()))

def jaccard(a: str, b: str) -> float:
    A, B = tokens(a), tokens(b)
    if not A and not B: return 1.0
    if not A or not B: return 0.0
    return len(A & B) / len(A | B)

def normalized_edit_distance(a: str, b: str) -> float:
    """Character Levenshtein distance divided by max character length."""
    left, right = str(a), str(b)
    if left == right: return 0.0
    if not left or not right: return 1.0
    previous = list(range(len(right) + 1))
    for i, char_left in enumerate(left, 1):
        current = [i]
        for j, char_right in enumerate(right, 1):
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (char_left != char_right)))
        previous = current
    return previous[-1] / max(len(left), len(right))

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("input", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    df = pd.read_csv(args.input).fillna("")
    if "generated_text" not in df or "anchor_text" not in df:
        raise ValueError("input needs anchor_text and generated_text")
    done = df[df.generated_text.astype(str).str.len().gt(0)].copy()
    corpus = pd.concat([done.anchor_text, done.generated_text], ignore_index=True).astype(str)
    tfidf = TfidfVectorizer(ngram_range=(1,2), min_df=1, sublinear_tf=True)
    tfidf.fit(corpus)
    jac, edit, cos = [], [], []
    for a,b in zip(done.anchor_text.astype(str), done.generated_text.astype(str)):
        jac.append(jaccard(a,b)); edit.append(normalized_edit_distance(a,b))
        X = tfidf.transform([a,b]); cos.append(float(cosine_similarity(X[0],X[1])[0,0]))
    done["lexical_jaccard"] = jac
    done["normalized_edit_distance"] = edit
    done["tfidf_cosine_similarity"] = cos
    done["combined_surface_distance"] = (
        1 - done.lexical_jaccard
        + done.normalized_edit_distance
        + 1 - done.tfidf_cosine_similarity
    ) / 3
    args.output.parent.mkdir(parents=True, exist_ok=True)
    done.to_csv(args.output, index=False)
    print(f"wrote {len(done)} measured variants")

if __name__ == "__main__":
    main()
