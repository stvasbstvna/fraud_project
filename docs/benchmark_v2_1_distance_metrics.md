# Benchmark v2.1 detector-independent linguistic distance

These metrics use only anchor and transformed text. Detector predictions, probabilities, coefficients, vocabularies, and errors are never inputs.

For lowercased alphanumeric/underscore token sets `A` and `B`:

`lexical_jaccard = |A ∩ B| / |A ∪ B|`.

Two empty sets have similarity 1; exactly one empty set has similarity 0.

Character edit distance is true Levenshtein distance normalized to `[0,1]`:

`normalized_edit_distance = levenshtein(anchor, variant) / max(len(anchor), len(variant))`.

TF–IDF cosine similarity is fitted independently on the complete measured anchor-plus-variant corpus with word unigrams/bigrams, `min_df=1`, sublinear TF, and L2 normalization. It is an analysis representation, not either frozen detector vectorizer:

`tfidf_cosine_similarity = cosine(tfidf(anchor), tfidf(variant))`.

The prespecified equal-weight surface index is:

`combined_surface_distance = ((1 - lexical_jaccard) + normalized_edit_distance + (1 - tfidf_cosine_similarity)) / 3`.

All four values are stored per completed variant. Corpus fitting and metric computation occur before detector outputs are read. Condition-level ordering is a manipulation check, not a basis for selecting messages by detector performance.
